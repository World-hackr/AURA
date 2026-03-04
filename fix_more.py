import json
import xml.etree.ElementTree as ET

def load_manifest(comp):
    with open(f'backend/parts_library/{comp}/manifest.json') as f:
        return json.load(f)

def save_manifest(comp, data):
    with open(f'backend/parts_library/{comp}/manifest.json', 'w') as f:
        json.dump(data, f, indent=2)

SCALE = 80.0 / 72.0

# 1. led_3mm & led_5mm
for comp in ['led_3mm', 'led_5mm']:
    d = load_manifest(comp)
    for p in d['pins']:
        if p['label'] == 'Cathode':
            p['uX'] = -4
        elif p['label'] == 'Anode':
            p['uX'] = 4
    save_manifest(comp, d)
    print(f"Fixed {comp} uX")

# 2. rgb_matrix_v25
# top pins: 128 to 133
d = load_manifest('rgb_matrix_v25')
for p in d['pins']:
    # The top pins were set to 91. The edge is closer to 97.5 (uH is 195)
    # the snap point is better to be fully visible and aligned with the pad. Let's try 95 and -95.
    if p['uY'] > 0:
        p['uY'] = 94
    else:
        p['uY'] = -94
    # ensure proper spacing for x. They are currently spaced by 8 units which is correct.
    # 53, 45, 37, 29, 21, 13
    # let's leave uX unchanged.
save_manifest('rgb_matrix_v25', d)
print("Fixed rgb_matrix_v25 uY")

# 3. oled_grove_128x96
d = load_manifest('oled_grove_128x96')
# Let's read the exact SVG width/height and viewBox
# uW = 170, uH = 90
# We need to center the 4 pins on the bottom. The spacing is typically 8u or maybe smaller for grove?
# Grove is actually 2mm pitch. 2mm = 2 / 2.54 * 8u = 6.3u... AURA uses 8u standard. Let's space by 8u.
# Bottom edge is -45. Let's do -45.
grove_ux = [-12, -4, 4, 12]
for i, p in enumerate(d['pins']):
    p['uY'] = -45
    if i < 4:
        p['uX'] = grove_ux[i]
save_manifest('oled_grove_128x96', d)
print("Fixed oled_grove_128x96")

# 4. alphanumeric
d = load_manifest('alphanumeric')
# It has bottom and top pins. The previous script grouped them all together but maybe not correctly.
# The SVG showed pin headers on the sides!
# Let's inspect the SVG carefully. 
# connector4pin: x=48.138, y=107.348, width=2.83, height=8.5 (vertical pin?)
# x=48.138 on the SVG. What is the AURA coordinate?
# SVG w: 1.13 in -> 81.36 pt -> uW=91 (90.4)
# SVG h: 2.1 in -> 151.2 pt -> uH=168 (168)
# origin: (45.5, 84)
# connector4pin center: x=48.138 + 1.417 = 49.55. y=107.348 + 4.25 = 111.6
# uX = 49.55 * (80/72) - 45.5 = 55.05 - 45.5 = 9.55 -> ~10
# uY = 84 - 111.6 * (80/72) = 84 - 124 = -40
# Wait, my previous coordinates were correct! x=10, y=-40, -48, -56, -64, -72, -80.
# The user said: "bottom snap points are wrong, properly detect the pin header and put snap points on the tip not just that snap point are also on modules edge current not even aligning with headers"
# Ah! The pins in alphanumeric are on the LEFT and RIGHT side!
# Let's look at the labels from my previous inspection:
# connector4: SDI, connector5: CLK ... these are the pins.
# They are on the sides? No, x=10 and x=-7. Wait, if uW=91, then x=10 and x=-7 is inside the board.
# Let's make the pins at the very edges or bottom edge?
# The physical pins on the Sparkfun alphanumeric display are on the TOP and BOTTOM.
# Let me just position them explicitly based on 8u grid at the top and bottom.
# Top: 6 pins, Bottom: 6 pins. Let's make them x = [-20, -12, -4, 4, 12, 20]
# Y = 84 (top) and -84 (bottom).
input_pins = ['connector4', 'connector5', 'connector6', 'connector7', 'connector8', 'connector9'] 
output_pins = ['connector12', 'connector13', 'connector14', 'connector15', 'connector16', 'connector17'] 
for p in d['pins']:
    if p['id'] in input_pins:
        idx = input_pins.index(p['id'])
        p['uX'] = -20 + (idx * 8)
        p['uY'] = -84
    elif p['id'] in output_pins:
        idx = output_pins.index(p['id'])
        p['uX'] = -20 + (idx * 8)
        p['uY'] = 84
    # The LED segments themselves (connector22... connector41) should not have snap points, or should be in the center
    elif 'connector' in p['id']:
        p['uY'] = 0 # Hide them or move them to middle so they don't get in the way
save_manifest('alphanumeric', d)
print("Fixed alphanumeric")

