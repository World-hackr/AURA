import json

# Absolute positions calculated directly from SVG
# width: 1.14299in (82.29528pt) -> 91.439u
# height: 2.1in (151.2pt) -> 168.0u
# viewBox is 0 0 82.2953 151.2. 
# scale is exact (1 pt = 1 pt). 
# AURA coordinates: uX = (cx * (80/72)) - 45.72, uY = 84.0 - (cy * (80/72))

def to_aura(cx, cy):
    scale = 80.0 / 72.0
    ux = (cx * scale) - 45.72
    uy = 84.0 - (cy * scale)
    return ux, uy

d = json.load(open('backend/parts_library/alphanumeric/manifest.json'))

pins = {
    'connector4': (49.555, 111.600),
    'connector5': (49.555, 118.800),
    'connector6': (49.555, 126.000),
    'connector7': (49.555, 133.200),
    'connector8': (49.555, 140.400),
    'connector9': (49.555, 147.600),
    'connector12': (34.724, 111.600),
    'connector13': (34.724, 118.800),
    'connector14': (34.724, 126.000),
    'connector15': (34.724, 133.200),
    'connector16': (34.724, 140.400),
    'connector17': (34.724, 147.600)
}

for p in d['pins']:
    if p['id'] in pins:
        cx, cy = pins[p['id']]
        ux, uy = to_aura(cx, cy)
        p['uX'] = round(ux, 3)
        p['uY'] = round(uy, 3)

with open('backend/parts_library/alphanumeric/manifest.json', 'w') as f:
    json.dump(d, f, indent=2)

print("Updated Alphanumeric pins with exact float coordinates.")
