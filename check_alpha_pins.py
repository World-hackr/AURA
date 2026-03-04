import xml.etree.ElementTree as ET
tree = ET.parse('backend/parts_library/alphanumeric/assets/AlphaNumericDisplay-v13_breadboard.svg')
root = tree.getroot()
for el in root.iter():
    eid = el.attrib.get('id', '')
    if 'connector' in eid and 'pin' in eid:
        print(f"{eid}: x={el.attrib.get('x')}, y={el.attrib.get('y')}, cx={el.attrib.get('cx')}, cy={el.attrib.get('cy')}")
