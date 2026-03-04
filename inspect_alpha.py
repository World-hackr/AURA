import xml.etree.ElementTree as ET
import re

tree = ET.parse('backend/parts_library/alphanumeric/assets/AlphaNumericDisplay-v13_breadboard.svg')
root = tree.getroot()

def get_transforms(el):
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

print('SVG size:', root.attrib.get('width'), root.attrib.get('height'), root.attrib.get('viewBox'))

for el in root.iter():
    eid = el.attrib.get('id', '')
    if 'connector' in eid and ('pin' in eid or 'pad' in eid):
        if el.tag.endswith('rect') or el.tag.endswith('circle') or el.tag.endswith('ellipse'):
            cx = float(el.attrib.get('cx', el.attrib.get('x', 0)))
            cy = float(el.attrib.get('cy', el.attrib.get('y', 0)))
            w = float(el.attrib.get('width', 0))
            h = float(el.attrib.get('height', 0))
            if el.tag.endswith('rect'):
                cx += w/2
                cy += h/2
            
            orig_cx, orig_cy = cx, cy
            transforms = get_transforms(el)
            for m in reversed(transforms):
                cx, cy = apply_matrix(cx, cy, m)
            
            tag_name = el.tag.split('}')[-1]
            print(f'{eid} ({tag_name}): center=({cx:.2f}, {cy:.2f}) [w={w:.2f}, h={h:.2f}]')
