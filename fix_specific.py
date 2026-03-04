import json
import os

def load_manifest(comp):
    path = f'backend/parts_library/{comp}/manifest.json'
    with open(path, 'r') as f:
        return json.load(f), path

def save_manifest(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# 1. rgb_matrix_v25 (top header row not snappable)
data, path = load_manifest('rgb_matrix_v25')
for p in data['pins']:
    if p['uY'] == 59:
        p['uY'] = 91 # Mirror of -91
save_manifest(path, data)

# 2. oled_wemos_d1_mini (right side pins not snappable)
data, path = load_manifest('oled_wemos_d1_mini')
right_pins = ['tx', 'rx', 'd1', 'd2', 'd3', 'd4', 'g', '5v']
for p in data['pins']:
    if p['id'] in right_pins:
        p['uX'] = 36 # Was -36
save_manifest(path, data)

# 3. oled_grove_128x96 (no snappable pins)
# Grove connector at bottom center. uW=170, uH=90.
# Let's put them at bottom edge (uY = -45), centered.
data, path = load_manifest('oled_grove_128x96')
grove_ux = [-12, -4, 4, 12]
for i, p in enumerate(data['pins']):
    p['uY'] = -45
    if i < 4:
        p['uX'] = grove_ux[i]
save_manifest(path, data)

# 4. nokia6100_lcd (top 4th pin not snappable)
# Add missing connector6 to the top row (uY=84)
data, path = load_manifest('nokia6100_lcd')
has_conn6 = any(p['id'] == 'connector6' for p in data['pins'])
if not has_conn6:
    data['pins'].append({
        'id': 'connector6',
        'uX': 8,
        'uY': 84,
        'label': 'VCC'
    })
save_manifest(path, data)

# 5. led_rgb_6pin (bottom three pins outside)
data, path = load_manifest('led_rgb_6pin')
for p in data['pins']:
    if p['uY'] == -28:
        p['uY'] = -24
save_manifest(path, data)

# 6. led_rgb_4pin (too below)
data, path = load_manifest('led_rgb_4pin')
for p in data['pins']:
    if p['uY'] == -42:
        p['uY'] = -18
save_manifest(path, data)

# 7. led_matrix_tx07 (pins invisible inside, move to edge)
data, path = load_manifest('led_matrix_tx07')
for p in data['pins']:
    if p['uX'] == -12:
        p['uX'] = -20
    elif p['uX'] == 12:
        p['uX'] = 20
save_manifest(path, data)

# 8. led_5mm & led_3mm (snap point way below)
for comp in ['led_5mm', 'led_3mm']:
    data, path = load_manifest(comp)
    for p in data['pins']:
        if p['uY'] == -44:
            p['uY'] = -16
    save_manifest(path, data)

# 9. alphanumeric (bottom male headers)
# uH is 168. Bottom is -84.
data, path = load_manifest('alphanumeric')
input_pins = ['connector4', 'connector5', 'connector6', 'connector7', 'connector8', 'connector9'] # SDI, CLK, LE, OE, VCC, GND
output_pins = ['connector12', 'connector13', 'connector14', 'connector15', 'connector16', 'connector17'] # SDO ...
# Let's place input pins horizontally at the bottom edge (uY=-84)
# Space them by 8 units. -20, -12, -4, 4, 12, 20
for p in data['pins']:
    if p['id'] in input_pins:
        idx = input_pins.index(p['id'])
        p['uX'] = -20 + (idx * 8)
        p['uY'] = -84
    elif p['id'] in output_pins:
        idx = output_pins.index(p['id'])
        p['uX'] = -20 + (idx * 8)
        p['uY'] = 84 # Top edge for outputs

save_manifest(path, data)

print("All specific component fixes applied.")
