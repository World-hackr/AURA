import xml.etree.ElementTree as ET

tree = ET.parse('backend/parts_library/arduino_nano/assets/breadboard.svg')
root = tree.getroot()
for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.attrib.get('id', '')
    if gid.startswith('led_'):
        print(f'Group: {gid}')
        for child in g.iter():
            tag = child.tag.split('}')[-1]
            if tag in ['path', 'rect', 'circle', 'ellipse']:
                print(f"  Child ID: {child.attrib.get('id')}, Fill: {child.attrib.get('fill')}, Tag: {tag}")
