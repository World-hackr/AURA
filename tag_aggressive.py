import xml.etree.ElementTree as ET
import os

def aggressive_tag(svg_path, mapping):
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    for old_id, new_id in mapping.items():
        # Find the group
        target_group = None
        for g in root.iter('{http://www.w3.org/2000/svg}g'):
            if g.attrib.get('id') == old_id:
                target_group = g
                break
        
        if target_group is not None:
            # Tag the group and EVERY descendant recursively
            target_group.attrib['id'] = new_id
            for el in target_group.iter():
                # Force every element to have an ID starting with new_id
                tag = el.tag.split('}')[-1]
                if tag in ['path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon']:
                    # We use a unique suffix to avoid duplicate IDs in the same file if needed, 
                    # but startswith is what the backend looks for.
                    el.attrib['id'] = f"{new_id}_part_{id(el)}"

    with open(svg_path, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)

# Nano
aggressive_tag('backend/parts_library/arduino_nano/assets/breadboard.svg', {
    'led_l': 'led_l',
    'led_pwr': 'led_pwr',
    'led_rx': 'led_rx',
    'led_tx': 'led_tx'
})

# Pro Mini - already tagged led_pwr and led_l manually, but let's be aggressive there too
aggressive_tag('backend/parts_library/arduino_pro_mini/assets/breadboard.svg', {
    'led_pwr': 'led_pwr',
    'led_l': 'led_l'
})

print("Aggressive tagging complete.")
