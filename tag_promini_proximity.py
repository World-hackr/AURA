import xml.etree.ElementTree as ET
import re

def get_transforms(el, parent_map, root):
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

svg_path = 'backend/parts_library/arduino_pro_mini/assets/breadboard.svg'
ET.register_namespace('', "http://www.w3.org/2000/svg")
tree = ET.parse(svg_path)
root = tree.getroot()
parent_map = {c: p for p in root.iter() for c in p}

# 1. Identify the reference green paths
targets = []
for el in root.iter():
    if str(el.attrib.get('fill', '')).upper() == '#22B573':
        cx, cy = 0, 0
        d = el.attrib.get('d', '')
        pts = re.findall(r'-?\d+\.?\d*', d)
        if pts:
            cx, cy = float(pts[0]), float(pts[1])
            ts = get_transforms(el, parent_map, root)
            for m in reversed(ts):
                cx, cy = apply_matrix(cx, cy, m)
            
            # Determine name based on Y (PWR is usually top/bottom depending on orientation)
            # Earlier scan: PWR was at y=87, L was at y=31. 
            name = "led_pwr" if cy > 60 else "led_l"
            targets.append({'name': name, 'cx': cx, 'cy': cy})

# 2. Tag every element near these points
counter = 0
for el in root.iter():
    tag = el.tag.split('}')[-1]
    if tag in ['rect', 'path', 'polygon', 'circle', 'ellipse']:
        cx, cy = 0, 0
        if tag == 'rect':
            cx = float(el.attrib.get('x', 0)) + float(el.attrib.get('width', 0))/2
            cy = float(el.attrib.get('y', 0)) + float(el.attrib.get('height', 0))/2
        elif tag == 'path':
            d = el.attrib.get('d', '')
            pts = re.findall(r'-?\d+\.?\d*', d)
            if pts: cx, cy = float(pts[0]), float(pts[1])
        
        ts = get_transforms(el, parent_map, root)
        for m in reversed(ts):
            cx, cy = apply_matrix(cx, cy, m)
            
        for t in targets:
            dist_sq = (cx - t['cx'])**2 + (cy - t['cy'])**2
            if dist_sq < 25: # 5px radius
                el.attrib['id'] = f"{t['name']}_part_{counter}"
                counter += 1

with open(svg_path, 'wb') as f:
    tree.write(f, encoding='utf-8', xml_declaration=True)

print(f"Tagged {counter} elements in Pro Mini LEDs based on proximity.")
