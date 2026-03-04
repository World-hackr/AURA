import xml.etree.ElementTree as ET

tree = ET.parse('backend/parts_library/alphanumeric/assets/AlphaNumericDisplay-v13_breadboard.svg')
root = tree.getroot()

print('Rectangles in SVG:')
for el in root.iter():
    if el.tag.endswith('rect'):
        print(f"Rect: x={el.attrib.get('x')}, y={el.attrib.get('y')}, w={el.attrib.get('width')}, h={el.attrib.get('height')}, fill={el.attrib.get('fill')}")
