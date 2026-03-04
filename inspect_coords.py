import json
import xml.etree.ElementTree as ET

print("--- rgb_matrix_v25 ---")
with open('backend/parts_library/rgb_matrix_v25/manifest.json') as f:
    d = json.load(f)
    for p in d['pins']:
        print(f"  {p['id']}: ({p['uX']}, {p['uY']})")

print("\n--- alphanumeric ---")
tree = ET.parse('backend/parts_library/alphanumeric/assets/AlphaNumericDisplay-v13_breadboard.svg')
for el in tree.getroot().iter():
    eid = el.attrib.get('id', '')
    if 'connector' in eid and 'pin' in eid:
        print(f"  {eid}: {el.attrib}")

print("\n--- oled_grove_128x96 ---")
tree = ET.parse('backend/parts_library/oled_grove_128x96/assets/seeed_grove_oled_128x96_breadboard.svg')
for el in tree.getroot().iter():
    eid = el.attrib.get('id', '')
    if 'connector' in eid:
        print(f"  {eid}: {el.attrib}")

print("\n--- led_3mm ---")
tree = ET.parse('backend/parts_library/led_3mm/assets/LED-3mm-red-leg.svg')
for el in tree.getroot().iter():
    eid = el.attrib.get('id', '')
    if 'connector' in eid and 'pin' in eid:
        print(f"  {eid}: {el.attrib}")

print("\n--- led_5mm ---")
tree = ET.parse('backend/parts_library/led_5mm/assets/LED-5mm-red-leg.svg')
for el in tree.getroot().iter():
    eid = el.attrib.get('id', '')
    if 'connector' in eid and 'pin' in eid:
        print(f"  {eid}: {el.attrib}")

