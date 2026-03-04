import json
import xml.etree.ElementTree as ET
import re

for comp in ['led_5mm', 'led_3mm']:
    # 1. Update manifest
    manifest_path = f'backend/parts_library/{comp}/manifest.json'
    with open(manifest_path, 'r') as f:
        d = json.load(f)
    
    # Change "Red LED - 5mm" to "LED - 5mm"
    d['label'] = d['label'].replace('Red ', '')
    
    with open(manifest_path, 'w') as f:
        json.dump(d, f, indent=2)

    # 2. Update SVG
    svg_name = f"LED-{comp.split('_')[1]}-red-leg.svg"
    svg_path = f'backend/parts_library/{comp}/assets/{svg_name}'
    
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    counter = 1
    for el in root.iter():
        fill = el.attrib.get('fill', '').upper()
        eid = el.attrib.get('id', '')
        
        # If the element is explicitly red, rename its ID to match the backend colorize logic
        if fill == '#E60000':
            el.attrib['id'] = f'led_glow_part{counter}'
            counter += 1

    with open(svg_path, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)

print("Updated LED manifests and SVGs for dynamic coloring.")
