import json
import xml.etree.ElementTree as ET
import re

SCALE = 80.0 / 72.0

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
    if not transform_str: return [1,0,0,1,0,0]
    match = re.search(r'matrix\(([^)]+)\)', transform_str)
    if match:
        parts = [float(x) for x in match.group(1).replace(',', ' ').split()]
        if len(parts) == 6:
            return parts
    match = re.search(r'translate\(([^)]+)\)', transform_str)
    if match:
        parts = [float(x) for x in match.group(1).replace(',', ' ').split()]
        if len(parts) == 1:
            return [1,0,0,1,parts[0], 0]
        elif len(parts) == 2:
            return [1,0,0,1,parts[0], parts[1]]
    return [1,0,0,1,0,0]

def apply_transform(x, y, matrix):
    a, b, c, d, e, f = matrix
    nx = a*x + c*y + e
    ny = b*x + d*y + f
    return nx, ny

def get_absolute_transform(el, parent_map):
    curr = el
    matrices = []
    while curr is not None:
        t_str = curr.attrib.get('transform', '')
        if t_str:
            matrices.append(parse_transform(t_str))
        curr = parent_map.get(curr)
    
    def apply_all(x, y):
        cx, cy = x, y
        for m in matrices:
            cx, cy = apply_transform(cx, cy, m)
        return cx, cy
    return apply_all

comp = 'oled_grove_128x96'
manifest_path = f'backend/parts_library/{comp}/manifest.json'
with open(manifest_path, 'r') as f:
    d = json.load(f)

tree = ET.parse(f'backend/parts_library/{comp}/assets/seeed_grove_oled_128x96_breadboard.svg')
root = tree.getroot()
parent_map = {c: p for p in root.iter() for c in p}

width_px = parse_dimension(root.attrib.get('width', '0'))
height_px = parse_dimension(root.attrib.get('height', '0'))
vb = root.attrib.get('viewBox', '').split()
vb_w = float(vb[2]) if vb else width_px
vb_h = float(vb[3]) if vb else height_px

scaleX = width_px / vb_w if vb_w else 1.0
scaleY = height_px / vb_h if vb_h else 1.0

uW = round(width_px * SCALE)
uH = round(height_px * SCALE)
originX = uW / 2.0
originY = uH / 2.0

print(f"uW: {uW}, uH: {uH}, originX: {originX}, originY: {originY}")

for pin in d['pins']:
    conn_id = pin['id']
    found_el = None
    for eid in [f"{conn_id}pin", f"{conn_id}pad", f"{conn_id}"]:
        for el in root.iter():
            if el.attrib.get('id') == eid:
                found_el = el
                break
        if found_el is not None: break
    
    if found_el is not None:
        tag = found_el.tag.split('}')[-1]
        
        if tag == 'path':
            # Extract x, y from path d string
            d_str = found_el.attrib.get('d', '')
            match = re.search(r'[mM]\s*([-\d\.]+)[,\s]+([-\d\.]+)', d_str)
            if match:
                cx = float(match.group(1))
                cy = float(match.group(2))
            else:
                cx, cy = 0, 0
        else:
            cx = float(found_el.attrib.get('cx', found_el.attrib.get('x', 0)))
            cy = float(found_el.attrib.get('cy', found_el.attrib.get('y', 0)))
            if 'width' in found_el.attrib and 'cx' not in found_el.attrib:
                cx += float(found_el.attrib.get('width', 0)) / 2
            if 'height' in found_el.attrib and 'cy' not in found_el.attrib:
                cy += float(found_el.attrib.get('height', 0)) / 2
        
        transform_fn = get_absolute_transform(found_el, parent_map)
        cx, cy = transform_fn(cx, cy)
        
        cx_doc = cx * scaleX
        cy_doc = cy * scaleY

        aura_x = round((cx_doc * SCALE) - originX)
        aura_y = round(originY - (cy_doc * SCALE))
        print(f"Pin {conn_id} ({pin['label']}): uX={aura_x}, uY={aura_y} (was {pin['uX']}, {pin['uY']})")
        pin['uX'] = aura_x
        pin['uY'] = aura_y

with open(manifest_path, 'w') as f:
    json.dump(d, f, indent=2)
