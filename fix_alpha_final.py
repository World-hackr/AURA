import json

manifest_path = 'backend/parts_library/alphanumeric/manifest.json'
with open(manifest_path, 'r') as f:
    d = json.load(f)

# Hardcode the precise snap points based on the physical features of the board.
# The user wants the snap points exactly at the TIPS of the headers.

# Right Header (Female, black box, pins 4-9) - Opening is on the right edge of the board.
# Right edge is uX = 46.
female_pins = ['connector4', 'connector5', 'connector6', 'connector7', 'connector8', 'connector9']
female_uy = [-40, -48, -56, -64, -72, -80]

# Left Header (Male, silver pins, pins 12-17) - Tip of silver pins is at uX = -23.
male_pins = ['connector12', 'connector13', 'connector14', 'connector15', 'connector16', 'connector17']
male_uy = [-40, -48, -56, -64, -72, -80]

# Middle LED Segment holes (pins 22-41)
# Right column: uX = 29
# Left column: uX = -27
segment_right = ['connector22', 'connector23', 'connector24', 'connector25', 'connector26', 'connector27', 'connector28', 'connector29', 'connector30', 'connector31']
segment_right_uy = [60, 52, 44, 36, 20, 12, -4, -12, -20, -28]

segment_left = ['connector32', 'connector33', 'connector34', 'connector35', 'connector36', 'connector37', 'connector38', 'connector39', 'connector40', 'connector41']
segment_left_uy = [-28, -20, -12, -4, 12, 20, 36, 44, 52, 60]

labels = {
    'connector4': 'SDI', 'connector5': 'CLK', 'connector6': 'LE', 'connector7': 'OE', 'connector8': 'VCC', 'connector9': 'GND',
    'connector12': 'SDO', 'connector13': 'CLK', 'connector14': 'LE', 'connector15': 'OE', 'connector16': 'VCC', 'connector17': 'GND',
    'connector22': '1', 'connector23': 'A1', 'connector24': 'H', 'connector25': 'F', 'connector26': 'VCC', 'connector27': 'G1', 'connector28': 'E', 'connector29': 'D1', 'connector30': 'N', 'connector31': 'M',
    'connector32': '13', 'connector33': 'D2', 'connector34': 'L', 'connector35': 'C', 'connector36': 'VCC', 'connector37': 'G2', 'connector38': 'B', 'connector39': 'A2', 'connector40': 'K', 'connector41': 'J'
}

pins = []

for i, pid in enumerate(female_pins):
    pins.append({'id': pid, 'uX': 46, 'uY': female_uy[i], 'label': labels[pid]})

for i, pid in enumerate(male_pins):
    pins.append({'id': pid, 'uX': -23, 'uY': male_uy[i], 'label': labels[pid]})

for i, pid in enumerate(segment_right):
    pins.append({'id': pid, 'uX': 29, 'uY': segment_right_uy[i], 'label': labels[pid]})

for i, pid in enumerate(segment_left):
    pins.append({'id': pid, 'uX': -27, 'uY': segment_left_uy[i], 'label': labels[pid]})

d['pins'] = pins

with open(manifest_path, 'w') as f:
    json.dump(d, f, indent=2)

print("Alphanumeric Display Driver fixed: Male tip at -23, Female tip at 46, LED holes restored.")
