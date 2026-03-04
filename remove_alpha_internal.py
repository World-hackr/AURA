import json

d = json.load(open('backend/parts_library/alphanumeric/manifest.json'))

# Filter out connector22 through connector41
valid_pins = []
for p in d['pins']:
    # Keep only the input/output headers
    if p['id'] in [f'connector{i}' for i in range(4, 10)] + [f'connector{i}' for i in range(12, 18)]:
        valid_pins.append(p)

d['pins'] = valid_pins

with open('backend/parts_library/alphanumeric/manifest.json', 'w') as f:
    json.dump(d, f, indent=2)

print("Removed internal LED segment pins from alphanumeric display.")
