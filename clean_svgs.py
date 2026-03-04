import xml.etree.ElementTree as ET
import glob
import os

resistor_svgs = glob.glob('backend/parts_library/resistor_*/assets/*.svg')

for svg_file in resistor_svgs:
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    # Namespaces make finding by id a bit trickier sometimes, so iterate all
    elements_to_remove = []
    
    for parent in root.iter():
        for child in list(parent):
            el_id = child.attrib.get('id', '')
            if 'Reflex' in el_id or 'Shadow' in el_id:
                elements_to_remove.append((parent, child))
                
    for parent, child in elements_to_remove:
        parent.remove(child)
        
    tree.write(svg_file, encoding='utf-8', xml_declaration=True)
    print(f"Cleaned {svg_file}")
