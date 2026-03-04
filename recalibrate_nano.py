import json
path = 'backend/parts_library/arduino_nano/manifest.json'
with open(path, 'r') as f:
    d = json.load(f)

# Correcting Nano Y-axis and assigning proper IDs for the dynamic SVG engine
d['indicators'] = [
    {"id": "led_l", "uX": 15, "uY": 38, "color": "#FFFF00"},
    {"id": "led_pwr", "uX": 4, "uY": 38, "color": "#00FF00"},
    {"id": "led_rx", "uX": -6, "uY": 38, "color": "#FFFF00"},
    {"id": "led_tx", "uX": -15, "uY": 38, "color": "#FFFF00"}
]

with open(path, 'w') as f:
    json.dump(d, f, indent=2)

print("Nano indicators recalibrated.")
