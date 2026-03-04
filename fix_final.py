import json

def load_manifest(comp):
    with open(f'backend/parts_library/{comp}/manifest.json') as f:
        return json.load(f)

def save_manifest(comp, data):
    with open(f'backend/parts_library/{comp}/manifest.json', 'w') as f:
        json.dump(data, f, indent=2)

# 1. Alphanumeric Display
# Put them exactly on the drawn headers inside the board.
d = load_manifest('alphanumeric')
input_pins = ['connector4', 'connector5', 'connector6', 'connector7', 'connector8', 'connector9'] 
output_pins = ['connector12', 'connector13', 'connector14', 'connector15', 'connector16', 'connector17'] 
for p in d['pins']:
    if p['id'] in input_pins:
        idx = input_pins.index(p['id'])
        p['uX'] = 10
        p['uY'] = -40 - (idx * 8)
    elif p['id'] in output_pins:
        idx = output_pins.index(p['id'])
        p['uX'] = -7
        p['uY'] = -40 - (idx * 8)
    # Put the LED segment pins exactly in the middle so they don't stick out
    elif 'connector' in p['id']:
        p['uY'] = 0
        p['uX'] = 0
save_manifest('alphanumeric', d)

# 2. Grove OLED 128x96
# Put them exactly on the Grove connector on the left side
d = load_manifest('oled_grove_128x96')
# Standard 8u pitch starting from -12 to 12
grove_y = [12, 4, -4, -12] # Ordering based on the path data: GND is top/bottom? 
# In script: 0(GND) was -12. 1(VCC) was -5 -> -4. 2(SDA) was 3 -> 4. 3(SCK) was 8 -> 12.
grove_y = [-12, -4, 4, 12]
for p in d['pins']:
    if p['id'] == 'connector0':
        p['uX'] = -65
        p['uY'] = -12
    elif p['id'] == 'connector1':
        p['uX'] = -65
        p['uY'] = -4
    elif p['id'] == 'connector2':
        p['uX'] = -65
        p['uY'] = 4
    elif p['id'] == 'connector3':
        p['uX'] = -65
        p['uY'] = 12
save_manifest('oled_grove_128x96', d)

print("Final snap points locked exactly to visual headers.")
