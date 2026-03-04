import xml.etree.ElementTree as ET
import re

tree = ET.parse('backend/parts_library/arduino_pro_mini/assets/breadboard.svg')
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

for el in root.iter():
    fill = str(el.attrib.get('fill', '')).upper()
    if fill in ['#FF0000', '#00FF00', '#22B573', '#FFD700', '#FFFF00', '#E60000']:
        eid = el.attrib.get('id', 'No ID')
        
        # calculate center
        cx = 0.0
        cy = 0.0
        if el.tag.endswith('rect'):
            x = float(el.attrib.get('x', 0))
            y = float(el.attrib.get('y', 0))
            w = float(el.attrib.get('width', 0))
            h = float(el.attrib.get('height', 0))
            cx = x + w/2
            cy = y + h/2
        elif el.tag.endswith('circle') or el.tag.endswith('ellipse'):
            cx = float(el.attrib.get('cx', 0))
            cy = float(el.attrib.get('cy', 0))
            
        transforms = get_transforms(el, parent_map)
        for m in reversed(transforms):
            cx, cy = apply_matrix(cx, cy, m)
            
        print(f'{el.tag} fill={fill}, id={eid}, cx={cx}, cy={cy}')
