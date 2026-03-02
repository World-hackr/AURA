import os
import json
import glob

def aurify_all():
    parts_dir = os.path.join(os.path.dirname(__file__), 'parts_library')
    
    # Dictionary of known good names and interactive mappings
    knowledge_base = {
        "16segment": {"label": "16-Segment Display", "sub": "Displays"},
        "7segment_100": {"label": "7-Segment Display (Large)", "sub": "Displays"},
        "alphanumeric": {"label": "Alphanumeric Display Driver", "sub": "Displays"},
        "alphanumeric_sparkfun": {"label": "SparkFun Alphanumeric Display", "sub": "Displays"},
        "color_lcd_shield": {"label": "Color LCD Shield", "sub": "Displays"},
        "duo_led_rg": {"label": "Bi-color LED (Red/Green)", "sub": "LEDs"},
        "fsr": {"label": "Force Sensitive Resistor (FSR)", "cat": "Sensor", "sub": "Force"},
        "glcd_128x64": {"label": "Graphic LCD 128x64", "sub": "Displays"},
        "grove_4digit_display": {"label": "Grove 4-Digit Display", "sub": "Displays"},
        "led_3mm": {"label": "Red LED - 3mm", "sub": "LEDs", "interactive": [{"type": "led", "action": "glow", "id": "led_glow", "label": "LED Lens"}]},
        "led_matrix_tx07": {"label": "LED Dot Matrix (TX07)", "sub": "Displays"},
        "led_rgb_4pin": {"label": "RGB LED (4-pin)", "sub": "LEDs", "interactive": [{"type": "rgb", "action": "glow", "id": "led_glow", "label": "RGB Lens"}]},
        "led_rgb_6pin": {"label": "RGB LED (6-pin)", "sub": "LEDs"},
        "lilypad_led": {"label": "LilyPad LED", "sub": "LEDs"},
        "nokia6100_lcd": {"label": "Nokia 6100 LCD", "sub": "Displays"},
        "oled_grove_128x96": {"label": "Grove OLED 128x96", "sub": "Displays"},
        "oled_wemos_d1_mini": {"label": "Wemos D1 Mini OLED", "sub": "Displays"},
        "resistor_5band": {"label": "Resistor (5-Band)", "cat": "Passive", "sub": "Resistors"},
        "rgb_matrix_v25": {"label": "RGB LED Matrix", "sub": "Displays"},
        "ws2812b": {"label": "SMD RGB LED (WS2812B)", "sub": "LEDs", "interactive": [{"type": "led", "action": "glow", "id": "led_glow", "label": "RGB Diode"}]}
    }

    for part in os.listdir(parts_dir):
        p_dir = os.path.join(parts_dir, part)
        if not os.path.isdir(p_dir): continue
        m_path = os.path.join(p_dir, 'manifest.json')
        if not os.path.exists(m_path): continue
        
        with open(m_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                continue
                
        changed = False
        
        # Apply Knowledge Base
        if part in knowledge_base:
            kb = knowledge_base[part]
            if 'label' in kb and data.get('label') != kb['label']:
                data['label'] = kb['label']
                changed = True
            if 'cat' in kb and data.get('category') != kb['cat']:
                data['category'] = kb['cat']
                changed = True
            if 'sub' in kb and data.get('sub_category') != kb['sub']:
                data['sub_category'] = kb['sub']
                changed = True
            if 'interactive' in kb and 'interactive' not in data:
                data['interactive'] = kb['interactive']
                changed = True
                
        # Fix categories generally
        cat = data.get('category', '')
        if cat == 'Passives': data['category'] = 'Passive'; changed = True
        if cat == 'MCU': data['category'] = 'Microcontroller'; changed = True
        
        # Determine component family for smart pin naming
        is_passive = 'resistor' in part or 'capacitor' in part or part == 'fsr'
        
        # Normalize Pins & Check for Floating Coordinates
        w = data.get('uW', 0)
        h = data.get('uH', 0)
        
        for pin in data.get('pins', []):
            old_l = pin.get('label', '')
            new_l = old_l.upper()
            
            # Common replacements
            if new_l == 'GND' or new_l == 'GROUND': new_l = 'GND'
            if new_l == 'VCC' or new_l == 'POWER': new_l = 'VCC'
            if new_l == 'R_W': new_l = 'RW'
            if new_l == 'RXI': new_l = 'RX'
            if new_l == 'TXO': new_l = 'TX'
            
            # Passives
            if is_passive:
                if new_l == '1' or new_l == '0': new_l = 'Terminal 1'
                if new_l == '2': new_l = 'Terminal 2'
                
            if old_l != new_l:
                pin['label'] = new_l
                changed = True
                
            # Coordinate sanity check
            ux = pin.get('uX', 0)
            uy = pin.get('uY', 0)
            
            # If a pin is more than 3x the width/height away from origin, it's floating
            if abs(ux) > (w * 1.5) or abs(uy) > (h * 1.5):
                print(f"  [Warning] {part} pin {pin['id']} is floating (uX:{ux}, uY:{uy}). Needs AI/Manual fix.")
                
        if changed:
            with open(m_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f'Aurified: {part}')

if __name__ == "__main__":
    aurify_all()
    print("Batch Aurification Complete!")
