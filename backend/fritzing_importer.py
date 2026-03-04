import xml.etree.ElementTree as ET
import json
import os
import glob
import re
from google import genai
from dotenv import load_dotenv

# Load API Key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY and GEMINI_API_KEY != "your_api_key_here":
    client = genai.Client(api_key=GEMINI_API_KEY)
    AI_ENABLED = True
else:
    print("Warning: GEMINI_API_KEY not set in .env. AI refinement will be skipped.")
    AI_ENABLED = False

def scan_svg_for_interactive_elements(svg_root):
    """
    Deterministically finds common dynamic elements in the SVG based on ID patterns.
    """
    interactive = []
    
    # Common Patterns
    patterns = {
        'led_glow': {'type': 'opacity', 'property': 'brightness', 'range': [0, 100], 'opacityRange': [0.1, 0.9]},
        'pot_dial': {'type': 'rotate', 'property': 'value', 'range': [0, 100], 'angleRange': [-135, 135]},
        'knob': {'type': 'rotate', 'property': 'value', 'range': [0, 100], 'angleRange': [-135, 135]},
        'plunger': {'type': 'translate', 'property': 'state', 'map': {'PRESSED': '0,2', 'RELEASED': '0,0'}},
        'seg': {'type': 'opacity', 'property': 'state', 'map': {'ON': 1.0, 'OFF': 0.1}}
    }

    for el in svg_root.iter():
        eid = el.attrib.get('id', '')
        if not eid: continue
        
        for key, config in patterns.items():
            if key in eid.lower():
                rule = {'id': eid}
                rule.update(config)
                # Avoid duplicates
                if not any(r['id'] == eid for r in interactive):
                    interactive.append(rule)
    
    return interactive

def aurify_with_ai(draft_json, fzp_text):
    """
    Uses Gemini to 'Aurify' the component data.
    """
    if not AI_ENABLED:
        return draft_json
    
    prompt = f"""
You are an expert Electronic Component Librarian for AURA.
Your task is to 'Aurify' a draft JSON representation of a Fritzing component.

AURA STANDARDS:
- Units (u): 1u = 0.3175mm (12.5 mils). 80u = 1 inch.
- Categories: [Microcontroller, Sensor, Actuator, Power, Passive, Optoelectronics, IC, Connector].

INTERACTIVE ARRAY SCHEMA:
We use an 'interactive' array of objects to define dynamic behaviors:
1. Rotation: {{"id": "svg_id", "type": "rotate", "property": "value", "range": [0, 100], "angleRange": [-135, 135]}}
2. Color: {{"id": "svg_id", "type": "color", "property": "color", "map": {{"Red": "#FF0000", ...}}}}
3. Opacity (LEDs/Glow): {{"id": "svg_id", "type": "opacity", "property": "brightness", "range": [0, 100], "opacityRange": [0.1, 0.9]}}

GOAL:
- VALIDATE pins against real-world datasheets.
- RENAME pins to official names (GND, VCC, D13, etc).
- IDENTIFY dynamic SVG IDs (led_glow, pot_dial, button_plunger) and add them to the 'interactive' array.
- Return ONLY the improved JSON. No chat.

INPUT:
1. Draft JSON:
{json.dumps(draft_json, indent=2)}

2. FZP Metadata:
{fzp_text[:2000]}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        improved_json = json.loads(text.strip())
        return improved_json
    except Exception as e:
        print(f"  !! AI Refinement failed: {e}")
        return draft_json

def parse_dimension(dim_str):
    dim_str = str(dim_str).strip().lower()
    if not dim_str: return 0.0
    match = re.match(r'([0-9\.]+)(in|mm|cm|px)?', dim_str)
    if not match: return 0.0
    val = float(match.group(1))
    unit = match.group(2)
    if unit == 'in': return val * 72.0
    elif unit == 'mm': return val * (72.0 / 25.4)
    elif unit == 'cm': return val * (72.0 / 2.54)
    else: return val

def import_fritzing_part(fzp_path, svg_path, component_folder_name, use_ai=False):
    SCALE = 80.0 / 72.0
    try:
        with open(fzp_path, 'r', encoding='utf-8') as f: fzp_content = f.read()
        root = ET.fromstring(fzp_content)
    except: return None

    title_el = root.find('title')
    title = title_el.text if title_el is not None else component_folder_name
    category = "Other"

    try:
        svg_tree = ET.parse(svg_path)
        svg_root = svg_tree.getroot()
    except: return None

    width_px = parse_dimension(svg_root.attrib.get('width', '0'))
    height_px = parse_dimension(svg_root.attrib.get('height', '0'))
    if width_px == 0 or height_px == 0:
        viewbox = svg_root.attrib.get('viewBox')
        if viewbox:
            parts = viewbox.replace(',', ' ').split()
            if len(parts) >= 4: width_px, height_px = float(parts[2]), float(parts[3])
    if width_px == 0: width_px = 100
    if height_px == 0: height_px = 100

    uW, uH = round(width_px * SCALE), round(height_px * SCALE)
    originX, originY = uW / 2, uH / 2

    pins = []
    connectors = root.find('connectors')
    if connectors is not None:
        for conn in connectors.findall('connector'):
            conn_id = conn.attrib.get('id')
            name = conn.attrib.get('name', conn_id)
            bb_view = conn.find(".//breadboardView/p")
            explicit_id = bb_view.attrib.get('svgId') if bb_view is not None else None
            
            search_ids = [explicit_id, f"{conn_id}pin", f"{conn_id}pad", f"{conn_id}leg", f"{conn_id}terminal"]
            found_el = next((el for el in svg_root.iter() if el.attrib.get('id') in search_ids), None)

            if found_el is not None:
                cx = float(found_el.attrib.get('cx', found_el.attrib.get('x', 0)))
                cy = float(found_el.attrib.get('cy', found_el.attrib.get('y', 0)))
                if 'width' in found_el.attrib and 'cx' not in found_el.attrib: cx += float(found_el.attrib.get('width')) / 2
                if 'height' in found_el.attrib and 'cy' not in found_el.attrib: cy += float(found_el.attrib.get('height')) / 2
                pins.append({
                    "id": conn_id,
                    "uX": round((cx * SCALE) - originX),
                    "uY": round(originY - (cy * SCALE)),
                    "label": name
                })

    # Standard scanning for interactive elements
    interactive = scan_svg_for_interactive_elements(svg_root)

    draft_result = {
        "type": component_folder_name,
        "label": title,
        "category": category,
        "views": {"breadboard": f"assets/{os.path.basename(svg_path)}", "schematic": None, "pcb": None},
        "uW": uW, "uH": uH, "originX": originX, "originY": originY,
        "pins": pins,
        "interactive": interactive
    }

    if use_ai and AI_ENABLED:
        return aurify_with_ai(draft_result, fzp_content)
    return draft_result

def run_bulk_import(use_ai=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parts_dir = os.path.join(base_dir, 'parts_library')
    for folder_name in os.listdir(parts_dir):
        folder_path = os.path.join(parts_dir, folder_name)
        if not os.path.isdir(folder_path): continue
        fzp_files = glob.glob(os.path.join(folder_path, 'fzp', '*.fzp'))
        svg_files = glob.glob(os.path.join(folder_path, 'assets', '*.svg'))
        if len(fzp_files) == 1 and len(svg_files) >= 1:
            manifest_path = os.path.join(folder_path, 'manifest.json')
            print(f"Processing: {folder_name}")
            manifest_data = import_fritzing_part(fzp_files[0], svg_files[0], folder_name, use_ai=use_ai)
            if manifest_data:
                with open(manifest_path, 'w', encoding='utf-8') as f: json.dump(manifest_data, f, indent=2)
                print(f"  -> Updated manifest.json")

if __name__ == "__main__":
    import sys
    run_bulk_import(use_ai="--ai" in sys.argv)
