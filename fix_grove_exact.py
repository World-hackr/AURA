import json

d = json.load(open('backend/parts_library/oled_grove_128x96/manifest.json'))
for p in d['pins']:
    if p['id'] == 'connector3':
        p['uX'] = -63.666
        p['uY'] = 9.646
    elif p['id'] == 'connector2':
        p['uX'] = -63.666
        p['uY'] = 1.774
    elif p['id'] == 'connector1':
        p['uX'] = -63.666
        p['uY'] = -6.124
    elif p['id'] == 'connector0':
        p['uX'] = -63.666
        p['uY'] = -14.000

with open('backend/parts_library/oled_grove_128x96/manifest.json', 'w') as f:
    json.dump(d, f, indent=2)

print("Updated oled_grove_128x96 with exact float coordinates.")
