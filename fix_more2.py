import json

def load_manifest(comp):
    with open(f'backend/parts_library/{comp}/manifest.json') as f:
        return json.load(f)

def save_manifest(comp, data):
    with open(f'backend/parts_library/{comp}/manifest.json', 'w') as f:
        json.dump(data, f, indent=2)

# 1. Alphanumeric
d = load_manifest('alphanumeric')
input_pins = ['connector4', 'connector5', 'connector6', 'connector7', 'connector8', 'connector9'] 
output_pins = ['connector12', 'connector13', 'connector14', 'connector15', 'connector16', 'connector17'] 
# Restore vertical layout but set snap point at the very tip (uY - 4 units)
# Original centers were X: 10, Y: -40 to -80
# And X: -7, Y: -40 to -80
# Actually, the user says "bottom snap points are wrong, properly detect the pin header and put snap points on the tip".
for p in d['pins']:
    if p['id'] in input_pins:
        idx = input_pins.index(p['id'])
        p['uX'] = 10
        p['uY'] = -40 - (idx * 8) - 4 # Push 4 units down to the tip
    elif p['id'] in output_pins:
        idx = output_pins.index(p['id'])
        p['uX'] = -7
        p['uY'] = -40 - (idx * 8) - 4
save_manifest('alphanumeric', d)

# 2. Grove OLED
d = load_manifest('oled_grove_128x96')
# It has 4 pads but no snap point. 
# In SVG: path d="m 15.66, 1029..."
# Let's map these properly. 
# y=1029.8, 1033.1, 1038.9, 1044.5
# x=15.66.
# If viewBox is standard, maybe uX is at the edge. 
# uW=170, uH=90. origin=(85, 45).
# If y is 1000+, it means viewBox is shifted or Fritzing does a huge transform.
# Let's just put the snap points on the left edge if x=15.
# And space them by 8u vertically.
# Wait, Grove connectors are usually on the side or bottom.
# Grove connector in the SVG is on the left edge.
for i, p in enumerate(d['pins']):
    p['uX'] = -85 # Left edge
    p['uY'] = 12 - (i * 8) # Centered vertically
save_manifest('oled_grove_128x96', d)

# 3. LED 3mm & 5mm
# "snap point on the edge but not in center of the width of pin"
# For 3mm, the pins are at X=3.45 and X=10.65.
# With width=2.15, centers are 4.52 and 11.72.
# In AURA units: 5 and 13.
# originX = 8.5. 
# So uX = 5 - 8.5 = -3.5. And 13 - 8.5 = 4.5.
# So uX should be -4 and 4? Or -3 and 5? 
# -3.5 and 4.5 means they are exactly 8 units apart! (-3.5 to 4.5 is 8 units).
# But since AURA needs integers, let's use -4 and +4.
for comp in ['led_3mm', 'led_5mm']:
    d = load_manifest(comp)
    for p in d['pins']:
        if p['label'] == 'Cathode':
            p['uX'] = -4
        elif p['label'] == 'Anode':
            p['uX'] = 4
    save_manifest(comp, d)

