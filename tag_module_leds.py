import xml.etree.ElementTree as ET
import json
import re

def aurify_module_leds(comp, svg_path, led_mappings):
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    for group_id, aura_id in led_mappings.items():
        # Find the group by ID
        for g in root.findall(f".//{{http://www.w3.org/2000/svg}}g[@id='{group_id}']"):
            # Tag the group itself and all paths inside it
            g.attrib['id'] = aura_id
            for child in g.iter():
                if child.tag.endswith('path') or child.tag.endswith('rect'):
                    child.attrib['id'] = f"{aura_id}_part"

    with open(svg_path, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)

# Arduino Nano Mappings (Found via previous inspection)
# X positions: 15(L), 4(PWR), -6(RX), -15(TX)
nano_leds = {
    'led-0603_2_': 'led_l',
    'led-0603_3_': 'led_pwr',
    'led-0603_5_': 'led_rx',
    'led-0603_4_': 'led_tx'
}
aurify_module_leds('arduino_nano', 'backend/parts_library/arduino_nano/assets/breadboard.svg', nano_leds)

# Arduino Pro Mini Mappings
# Found two #22B573 paths earlier. I will tag them.
tree = ET.parse('backend/parts_library/arduino_pro_mini/assets/breadboard.svg')
root = tree.getroot()
counter = 0
for el in root.iter():
    if el.attrib.get('fill') == '#22B573':
        el.attrib['id'] = 'led_pwr' if counter == 0 else 'led_l'
        counter += 1
with open('backend/parts_library/arduino_pro_mini/assets/breadboard.svg', 'wb') as f:
    tree.write(f, encoding='utf-8', xml_declaration=True)

print("Module SVGs updated with LED IDs.")
