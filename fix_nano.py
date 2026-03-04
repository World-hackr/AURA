import json

path = 'backend/parts_library/arduino_nano/manifest.json'
with open(path, 'r') as f:
    d = json.load(f)

d['indicators'] = [
    {"id": "L", "uX": 15, "uY": -26, "color": "#22B573"},
    {"id": "PWR", "uX": 4, "uY": -26, "color": "#22B573"},
    {"id": "RX", "uX": -6, "uY": -26, "color": "#22B573"},
    {"id": "TX", "uX": -15, "uY": -26, "color": "#22B573"}
]

with open(path, 'w') as f:
    json.dump(d, f, indent=2)

print("Nano indicators added.")
