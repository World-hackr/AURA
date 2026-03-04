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

elements = []
for el in root.iter():
    tag = el.tag.split('}')[-1]
    if tag in ['rect', 'path']:
        cx, cy = 0, 0
        if tag == 'rect':
            cx = float(el.attrib.get('x', 0)) + float(el.attrib.get('width', 0))/2
            cy = float(el.attrib.get('y', 0)) + float(el.attrib.get('height', 0))/2
        elif tag == 'path':
            d = el.attrib.get('d', '')
            pts = re.findall(r'-?\d+\.?\d*', d)
            if pts: cx, cy = float(pts[0]), float(pts[1])
        
        ts = get_transforms(el, parent_map)
        for m in reversed(ts):
            cx, cy = apply_matrix(cx, cy, m)
        
        elements.append({'tag': tag, 'id': el.attrib.get('id'), 'fill': el.attrib.get('fill'), 'cx': cx, 'cy': cy})

# Find the green ones
greens = [e for e in elements if str(e['fill']).upper() == '#22B573']
for g in greens:
    print(f"GREEN: {g}")
    # find neighbors
    for e in elements:
        dist = (e['cx'] - g['cx'])**2 + (e['cy'] - g['cy'])**2
        if dist < 10 and e != g:
            print(f"  Neighbor: {e}")
