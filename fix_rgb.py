import json

def load_manifest(comp):
    with open(f'backend/parts_library/{comp}/manifest.json') as f:
        return json.load(f)

def save_manifest(comp, data):
    with open(f'backend/parts_library/{comp}/manifest.json', 'w') as f:
        json.dump(data, f, indent=2)

# Fix rgb_matrix_v25
d = load_manifest('rgb_matrix_v25')
top_pins = ['connector128', 'connector129', 'connector130', 'connector131', 'connector132', 'connector133']
bottom_pins = ['connector134', 'connector135', 'connector136', 'connector137', 'connector138', 'connector139']
xs = [20, 12, 4, -4, -12, -20]

for p in d['pins']:
    if p['id'] in top_pins:
        p['uX'] = xs[top_pins.index(p['id'])]
        p['uY'] = 94
    elif p['id'] in bottom_pins:
        p['uX'] = xs[bottom_pins.index(p['id'])]
        p['uY'] = -94

save_manifest('rgb_matrix_v25', d)
print("rgb_matrix_v25 fully fixed")
