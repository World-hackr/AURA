import os
import json
import glob
import re

def normalize_pin_name(old_name):
    name = old_name.upper().strip()
    # Remove generic fritzing artifacts
    name = re.sub(r'^CONNECTOR\d+', '', name)
    name = re.sub(r'PIN$', '', name)
    name = re.sub(r'PAD$', '', name)
    name = name.strip()
    
    # Standard mappings
    mappings = {
        'GND': 'GND', 'GROUND': 'GND', '-': 'GND', 'MINUS': 'GND', 'VSS': 'GND',
        'VCC': 'VCC', 'POWER': 'VCC', '+': 'VCC', 'PLUS': 'VCC', 'VDD': 'VCC', '5V': '5V', '3V3': '3.3V', '3.3V': '3.3V',
        'RXI': 'RX', 'RXD': 'RX', 'TXO': 'TX', 'TXD': 'TX',
        'SCL': 'SCK', 'CLOCK': 'SCK',
        'SDA': 'SDA', 'DATA': 'SDA',
        'R_W': 'RW', 'R/W': 'RW',
        'ANODE': 'Anode', 'CATHODE': 'Cathode'
    }
    
    for k, v in mappings.items():
        if name == k:
            return v
            
    if not name:
        return old_name # Fallback
    return name

def aurify_all():
    parts_dir = os.path.join(os.path.dirname(__file__), 'parts_library')
    
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
        
        # General Category Fixes
        cat = data.get('category', '')
        if cat == 'Passives': data['category'] = 'Passive'; changed = True
        if cat == 'MCU': data['category'] = 'Microcontroller'; changed = True
        
        is_passive = 'resistor' in part or 'capacitor' in part or part == 'fsr'
        
        # Normalize Pins
        for pin in data.get('pins', []):
            old_l = pin.get('label', '')
            new_l = normalize_pin_name(old_l)
            
            # Special override for passives
            if is_passive:
                if '1' in old_l or '0' in old_l: new_l = 'Terminal 1'
                elif '2' in old_l: new_l = 'Terminal 2'
                
            if old_l != new_l:
                pin['label'] = new_l
                changed = True
                
        if changed:
            with open(m_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f'Aurified & Normalized: {part}')

if __name__ == "__main__":
    aurify_all()
    print("Batch Aurification Complete!")
