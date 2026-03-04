import xml.etree.ElementTree as ET
import re
import json

SCALE = 80.0 / 72.0

def get_transforms(el, parent_map):
    transforms = []
    p = parent_map.get(el)
    while p is not None:
        t = p.attrib.get('transform')
        if t:
            match = re.search(r'matrix\(([^)]+)\)', t)
            if match:
                parts = [float(x) for x in match.group(1).replace(',', ' ').split()]
                transforms.append(parts)
        p = parent_map.get(p)
    return transforms

def apply_matrix(x, y, matrix):
    a, b, c, d, e, f = matrix
    return a*x + c*y + e, b*x + d*y + f

tree = ET.parse('backend/parts_library/arduino_pro_mini/assets/breadboard.svg')
root = tree.getroot()
parent_map = {c: p for p in root.iter() for c in p}

w_px = 72.0 * 0.7 # approx 50
h_px = 72.0 * 1.3 # approx 93.6

uW = round(w_px * SCALE)
uH = round(h_px * SCALE)
originX = uW / 2.0
originY = uH / 2.0

found = []
for el in root.iter():
    fill = str(el.attrib.get('fill', '')).upper()
    if fill == '#22B573':
        d_str = el.attrib.get('d', '')
        if d_str:
            coords = [float(c) for c in re.findall(r'-?\d+\.?\d*', d_str)]
            if len(coords) > 2:
                cx = coords[0]
                cy = coords[1]
                transforms = get_transforms(el, parent_map)
                for m in reversed(transforms):
                    cx, cy = apply_matrix(cx, cy, m)
                
                ux = round((cx * SCALE) - originX)
                uy = round(originY - (cy * SCALE))
                found.append({'uX': ux, 'uY': uy})

print(found)

path = 'backend/parts_library/arduino_pro_mini/manifest.json'
with open(path, 'r') as f:
    d = json.load(f)

# The list 'found' contains two objects.
# Let's say first is PWR, second is L.
if len(found) >= 2:
    # Let's assign IDs based on their Y position.
    # The higher Y (smaller uy physically, larger Y coordinate) is probably one or the other.
    d['indicators'] = [
        {"id": "PWR", "uX": found[0]['uX'], "uY": found[0]['uY'], "color": "#22B573"},
        {"id": "L", "uX": found[1]['uX'], "uY": found[1]['uY'], "color": "#22B573"}
    ]
    with open(path, 'w') as f:
        json.dump(d, f, indent=2)
    print("Pro Mini indicators added.")
