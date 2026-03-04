import os
import json
import re
import xml.etree.ElementTree as ET

def parse_dimension(dim_str):
    dim_str = str(dim_str).strip().lower()
    if not dim_str: return 0.0
    match = re.match(r'([0-9\.]+)(in|mm|cm|px)?', dim_str)
    if not match: return 0.0
    val = float(match.group(1))
    unit = match.group(2)
    if unit == 'in': return val * 72.0
    elif unit == 'mm': return val * (72.0 / 25.4)
    elif unit == 'cm': return val * (72.0 / 2.54)
    else: return val

def parse_transform(transform_str):
    dx, dy = 0.0, 0.0
    if not transform_str: return dx, dy
    matches = re.finditer(r'translate\(([-\d\.]+)[,\s]+([-\d\.]+)\)', transform_str)
    for m in matches:
        dx += float(m.group(1))
        dy += float(m.group(2))
    return dx, dy

def get_absolute_transform(el, parent_map):
    dx, dy = 0.0, 0.0
    curr = el
    while curr is not None:
        t_str = curr.attrib.get('transform', '')
        if t_str:
            tx, ty = parse_transform(t_str)
            dx += tx
            dy += ty
        curr = parent_map.get(curr)
    return dx, dy

SCALE = 80.0 / 72.0
base_dir = os.path.dirname(os.path.abspath(__file__))
parts_dir = os.path.join(base_dir, 'backend', 'parts_library')

for folder_name in os.listdir(parts_dir):
    folder_path = os.path.join(parts_dir, folder_name)
    if not os.path.isdir(folder_path): continue
    
    manifest_path = os.path.join(folder_path, 'manifest.json')
    if not os.path.exists(manifest_path): continue

    with open(manifest_path, 'r', encoding='utf-8') as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError:
            continue

    # Skip dynamic or missing SVGs
    bb = manifest.get('views', {}).get('breadboard')
    if bb == 'dynamic' or not bb:
        continue

    svg_rel = bb
    if svg_rel.startswith(folder_name + '/'):
        svg_rel = svg_rel[len(folder_name)+1:]
    
    svg_path = os.path.join(folder_path, svg_rel)
    if not os.path.exists(svg_path):
        continue

    try:
        svg_tree = ET.parse(svg_path)
        svg_root = svg_tree.getroot()
    except Exception:
        continue

    parent_map = {c: p for p in svg_root.iter() for c in p}

    width_px = parse_dimension(svg_root.attrib.get('width', '0'))
    height_px = parse_dimension(svg_root.attrib.get('height', '0'))
    
    vb_w, vb_h = width_px, height_px
    viewbox = svg_root.attrib.get('viewBox')
    if viewbox:
        parts = viewbox.replace(',', ' ').split()
        if len(parts) >= 4:
            vb_w = float(parts[2])
            vb_h = float(parts[3])

    if width_px == 0: width_px = 100
    if height_px == 0: height_px = 100
    if vb_w == 0: vb_w = width_px
    if vb_h == 0: vb_h = height_px

    scaleX = width_px / vb_w if vb_w else 1.0
    scaleY = height_px / vb_h if vb_h else 1.0

    uW = round(width_px * SCALE)
    uH = round(height_px * SCALE)
    
    originX = manifest.get('originX', uW / 2.0)
    originY = manifest.get('originY', uH / 2.0)
    
    changed = False
    
    for pin in manifest.get('pins', []):
        conn_id = pin.get('id')
        if not conn_id: continue
        
        search_ids = [
            f"{conn_id}terminal",
            f"{conn_id}leg",
            f"{conn_id}pin",
            f"{conn_id}pad"
        ]

        found_el = None
        for target_id in search_ids:
            for el in svg_root.iter():
                eid = el.attrib.get('id', '')
                if eid.split(':')[-1] == target_id:
                    found_el = el
                    break
            if found_el is not None:
                break
        
        if found_el is not None:
            tag = found_el.tag.split('}')[-1]
            
            tx, ty = get_absolute_transform(found_el, parent_map)

            if tag == 'line':
                x1 = float(found_el.attrib.get('x1', 0))
                y1 = float(found_el.attrib.get('y1', 0))
                x2 = float(found_el.attrib.get('x2', 0))
                y2 = float(found_el.attrib.get('y2', 0))
                
                x1 += tx; y1 += ty
                x2 += tx; y2 += ty
                
                cx_center = vb_w / 2
                cy_center = vb_h / 2
                dist1 = (x1 - cx_center)**2 + (y1 - cy_center)**2
                dist2 = (x2 - cx_center)**2 + (y2 - cy_center)**2
                
                if dist2 > dist1:
                    cx, cy = x2, y2
                else:
                    cx, cy = x1, y1
                    
            else:
                cx = float(found_el.attrib.get('cx', found_el.attrib.get('x', 0)))
                cy = float(found_el.attrib.get('cy', found_el.attrib.get('y', 0)))

                if 'width' in found_el.attrib and 'cx' not in found_el.attrib:
                    cx += float(found_el.attrib.get('width', 0)) / 2
                if 'height' in found_el.attrib and 'cy' not in found_el.attrib:
                    cy += float(found_el.attrib.get('height', 0)) / 2
                cx += tx
                cy += ty
            
            cx_doc = cx * scaleX
            cy_doc = cy * scaleY

            aura_x = round((cx_doc * SCALE) - originX)
            aura_y = round(originY - (cy_doc * SCALE))
            
            if pin.get('uX') != aura_x or pin.get('uY') != aura_y:
                print(f"[{folder_name}] Pin {conn_id} ({pin.get('label')}) moved from ({pin.get('uX')}, {pin.get('uY')}) to ({aura_x}, {aura_y}) based on <{tag}>")
                pin['uX'] = aura_x
                pin['uY'] = aura_y
                changed = True

    if changed:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        print(f"Updated snap points for {folder_name}")

print("Done.")