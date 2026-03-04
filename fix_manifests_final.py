import json

# Fix Nano
path = 'backend/parts_library/arduino_nano/manifest.json'
with open(path, 'r') as f:
    d = json.load(f)
d['indicators'] = [
    {"id": "led_l", "uX": 15, "uY": 26, "color": "#FFFF00"},
    {"id": "led_pwr", "uX": 4, "uY": 26, "color": "#00FF00"},
    {"id": "led_rx", "uX": -6, "uY": 26, "color": "#FFFF00"},
    {"id": "led_tx", "uX": -15, "uY": 26, "color": "#FFFF00"}
]
with open(path, 'w') as f:
    json.dump(d, f, indent=2)

# Fix Pro Mini
path = 'backend/parts_library/arduino_pro_mini/manifest.json'
with open(path, 'r') as f:
    d = json.load(f)
# Earlier scan: ID: led_pwr, AURA: (13, -45); ID: led_l, AURA: (-2, 17)
d['indicators'] = [
    {"id": "led_pwr", "uX": 13, "uY": -45, "color": "#00FF00"},
    {"id": "led_l", "uX": -2, "uY": 17, "color": "#FFFF00"}
]
with open(path, 'w') as f:
    json.dump(d, f, indent=2)

print("Manifests updated with correct Y-axis and IDs.")
