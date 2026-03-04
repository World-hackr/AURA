import xml.etree.ElementTree as ET

tree = ET.parse('backend/parts_library/arduino_pro_mini/assets/breadboard.svg')
root = tree.getroot()
for el in root.iter():
    eid = el.attrib.get('id', '')
    if eid.startswith('led_'):
        tag = el.tag.split('}')[-1]
        print(f"Element: {eid}, Tag: {tag}, Fill: {el.attrib.get('fill')}")
