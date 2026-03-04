import xml.etree.ElementTree as ET
import re

tree = ET.parse('backend/parts_library/arduino_nano/assets/breadboard.svg')
root = tree.getroot()

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

parent_map = {c: p for p in root.iter() for c in p}

SCALE = 80.0 / 72.0
originX, originY = 28.0, 68.0

for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.attrib.get('id', '')
    if gid in ['led_l', 'led_pwr', 'led_rx', 'led_tx']:
        # Average all child bounding boxes
        found = False
        for child in g.iter():
            tag = child.tag.split('}')[-1]
            if tag == 'rect':
                cx = float(child.attrib.get('x', 0)) + float(child.attrib.get('width', 0))/2
                cy = float(child.attrib.get('y', 0)) + float(child.attrib.get('height', 0))/2
                
                ts = get_transforms(child, parent_map)
                for m in reversed(ts):
                    cx, cy = apply_matrix(cx, cy, m)
                
                ux = (cx * SCALE) - originX
                uy = originY - (cy * SCALE)
                print(f"ID: {gid}, AURA: ({ux:.2f}, {uy:.2f})")
                found = True
                break
