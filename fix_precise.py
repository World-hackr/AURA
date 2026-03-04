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
        # SVG applies transforms from child up to root
        for m in matrices:
            cx, cy = apply_transform(cx, cy, m)
        return cx, cy
    return apply_all

def fix_component(comp, svg_name):
    manifest_path = f'backend/parts_library/{comp}/manifest.json'
    with open(manifest_path, 'r') as f:
        d = json.load(f)

    tree = ET.parse(f'backend/parts_library/{comp}/assets/{svg_name}')
    root = tree.getroot()
    parent_map = {c: p for p in root.iter() for c in p}

    width_px = parse_dimension(root.attrib.get('width', '0'))
    height_px = parse_dimension(root.attrib.get('height', '0'))
    vb = root.attrib.get('viewBox', '').split()
    if vb:
        vb_w = float(vb[2])
        vb_h = float(vb[3])
    else:
        vb_w = width_px
        vb_h = height_px

    scaleX = width_px / vb_w if vb_w else 1.0
    scaleY = height_px / vb_h if vb_h else 1.0

    uW = round(width_px * SCALE)
    uH = round(height_px * SCALE)
    originX = uW / 2.0
    originY = uH / 2.0

    for pin in d['pins']:
        conn_id = pin['id']
        found_el = None
        for eid in [f"{conn_id}pin", f"{conn_id}pad", conn_id]:
            for el in root.iter():
                if el.attrib.get('id') == eid:
                    found_el = el
                    break
            if found_el is not None: break
        
        if found_el is not None:
            tag = found_el.tag.split('}')[-1]
            
            if tag == 'path':
                # Bounding box of path is complex, but we can do a naive center of all move/line points
                d_str = found_el.attrib.get('d', '')
                coords = re.findall(r'[-\d\.]+', d_str)
                coords = [float(c) for c in coords]
                if len(coords) >= 2:
                    # just take the first coordinate and assume it's the corner, or average all X and Y
                    # For a square path like "m 15.66 1029.8 0 -2.26 2.26 0 0 2.26 -2.26 0"
                    # The first point is 15.66, 1029.8.
                    # The square is 2.26x2.26. 
                    # If we average the absolute points (which are relative after m!)
                    # Let's just do a naive regex to see if it's the grove path
                    if comp == 'oled_grove_128x96':
                        # The start point is m X, Y. Then it draws a box.
                        # For oled_grove_128x96, they are 2.26 units wide.
                        cx = coords[0] + 1.13
                        cy = coords[1] - 1.13
                        if conn_id == 'connector2': # starts at 17.93 and draws left
                            cx = coords[0] - 1.13
                    else:
                        cx, cy = coords[0], coords[1]
                else:
                    cx, cy = 0, 0
            elif tag in ['rect', 'circle', 'ellipse']:
                cx = float(found_el.attrib.get('cx', found_el.attrib.get('x', 0)))
                cy = float(found_el.attrib.get('cy', found_el.attrib.get('y', 0)))
                if tag == 'rect':
                    if 'width' in found_el.attrib and 'cx' not in found_el.attrib:
                        cx += float(found_el.attrib.get('width', 0)) / 2
                    if 'height' in found_el.attrib and 'cy' not in found_el.attrib:
                        cy += float(found_el.attrib.get('height', 0)) / 2
            else:
                cx, cy = 0, 0
            
            transform_fn = get_absolute_transform(found_el, parent_map)
            cx, cy = transform_fn(cx, cy)
            
            cx_doc = cx * scaleX
            cy_doc = cy * scaleY

            aura_x = round((cx_doc * SCALE) - originX)
            aura_y = round(originY - (cy_doc * SCALE))
            print(f"{comp} {conn_id} ({pin['label']}): uX={aura_x}, uY={aura_y}")
            pin['uX'] = aura_x
            pin['uY'] = aura_y

    with open(manifest_path, 'w') as f:
        json.dump(d, f, indent=2)

fix_component('alphanumeric', 'AlphaNumericDisplay-v13_breadboard.svg')
fix_component('oled_grove_128x96', 'seeed_grove_oled_128x96_breadboard.svg')
