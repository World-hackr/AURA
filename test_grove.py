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

tree = ET.parse('backend/parts_library/oled_grove_128x96/assets/seeed_grove_oled_128x96_breadboard.svg')
root = tree.getroot()

def apply_transform(x, y, matrix):
    a, b, c, d, e, f = matrix
    nx = a*x + c*y + e
    ny = b*x + d*y + f
    return nx, ny

def get_transforms(el):
    transforms = []
    curr = el
    parent_map = {c: p for p in root.iter() for c in p}
    while curr is not None:
        t_str = curr.attrib.get('transform', '')
        if t_str:
            match = re.search(r'matrix\(([^)]+)\)', t_str)
            if match:
                parts = [float(x) for x in match.group(1).replace(',', ' ').split()]
                transforms.append(parts)
        curr = parent_map.get(curr)
    return transforms

width_px = parse_dimension(root.attrib.get('width', '0'))
height_px = parse_dimension(root.attrib.get('height', '0'))

vb = root.attrib.get('viewBox', '')
print("VIEWBOX:", vb)
print("W,H:", width_px, height_px)

uW = round(width_px * SCALE)
uH = round(height_px * SCALE)
originX = uW / 2.0
originY = uH / 2.0

for el in root.iter():
    eid = el.attrib.get('id', '')
    if eid in ['connector0pin', 'connector1pin', 'connector2pin', 'connector3pin']:
        d_str = el.attrib.get('d', '')
        coords = [float(c) for c in re.findall(r'[-\d\.]+', d_str)]
        
        # It's a square path: m x,y 0,-2.26 2.26,0 0,2.26 -2.26,0
        if len(coords) >= 2:
            x = coords[0]
            y = coords[1]
            
            # The coordinates are relative. The drawn box is from x to x+2.26 and y to y-2.26 (or similar)
            # The center is roughly x + 1.13, y - 1.13 (or y + 1.13)
            # Let's just find the bounding box of the absolute coordinates of the path
            
            cx = x + 1.133
            if eid in ['connector3pin', 'connector2pin']: # from looking at earlier traces
                cy = y - 1.133
            else:
                cy = y + 1.133
                
            if eid == 'connector2pin':
                cx = x - 1.133
            
            # actually let's just print the transforms and do it right
            ts = get_transforms(el)
            print(f"--- {eid} ---")
            print("Local start:", x, y)
            print("Transforms:", ts)
            
            tx, ty = cx, cy
            for m in reversed(ts): # child up to root
                tx, ty = apply_transform(tx, ty, m)
                
            aura_x = round((tx * (width_px / width_px)) * SCALE - originX)
            aura_y = round(originY - (ty * (height_px / height_px)) * SCALE)
            print("Absolute:", tx, ty)
            print("AURA:", aura_x, aura_y)
