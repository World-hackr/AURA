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

def process_svg(comp, svg_path, colors):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    parent_map = {c: p for p in root.iter() for c in p}
    
    w_px = float(root.attrib.get('width', '100').replace('in','')) * 72.0 if 'in' in root.attrib.get('width','') else float(root.attrib.get('width', '100').replace('px',''))
    h_px = float(root.attrib.get('height', '100').replace('in','')) * 72.0 if 'in' in root.attrib.get('height','') else float(root.attrib.get('height', '100').replace('px',''))
    
    uW = round(w_px * SCALE)
    uH = round(h_px * SCALE)
    originX = uW / 2.0
    originY = uH / 2.0
    
    found = []
    for el in root.iter():
        fill = str(el.attrib.get('fill', '')).upper()
        if fill in colors:
            cx, cy = 0, 0
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
            elif el.tag.endswith('path'):
                d_str = el.attrib.get('d', '')
                coords = [float(c) for c in re.findall(r'[-\d\.]+', d_str)]
                if len(coords) > 2:
                    cx = coords[0]
                    cy = coords[1]
            
            transforms = get_transforms(el, parent_map)
            for m in reversed(transforms):
                cx, cy = apply_matrix(cx, cy, m)
            
            ux = round((cx * SCALE) - originX)
            uy = round(originY - (cy * SCALE))
            found.append({'color': fill, 'uX': ux, 'uY': uy})
    return found

print("Nano:", process_svg('arduino_nano', 'backend/parts_library/arduino_nano/assets/breadboard.svg', ['#22B573', '#FFFF00', '#FF0000']))
print("Pro Mini:", process_svg('arduino_pro_mini', 'backend/parts_library/arduino_pro_mini/assets/breadboard.svg', ['#22B573', '#FFFF00', '#FF0000']))
