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

def aurify_with_ai(draft_json, fzp_text):
    """
    Uses Gemini to 'Aurify' the component data.
    It takes the basic parsed JSON and the raw FZP description to improve labels, 
    categorization, and general metadata.
    """
    if not AI_ENABLED:
        return draft_json
    
    prompt = f"""
You are an expert Electronic Component Librarian for AURA (a professional circuit designer).
Your task is to 'Aurify' a draft JSON representation of a Fritzing component by cross-referencing it with OFFICIAL DATASHEETS.

AURA STANDARDS:
- Units (u): 1u = 0.3175mm (12.5 mils). Standard pitch is 8u (2.54mm).
- Pin Labels: Use OFFICIAL MANUFACTURER NAMES from datasheets (e.g., 'GND', 'VCC', 'PB5/SCK', 'AREF'). 
- Categories: [Microcontroller, Sensor, Actuator, Power, Passive, Optoelectronics, IC, Connector, Other].

INTERACTIVE ELEMENTS (The 'Digital Twin' Feature):
- Identify SVG IDs that represent parts that move or glow.
- LEDs: Find the ID of the 'lens' or 'glow' part.
- Buttons/Switches: Find the ID of the 'plunger' or 'toggle'.
- Displays: Identify IDs for individual segments (e.g., 'segA', 'segB').
- Motors: Find the ID of the 'shaft'.

INPUT DATA:
1. Draft JSON:
{json.dumps(draft_json, indent=2)}

2. FZP Raw Metadata (for context):
{fzp_text[:2000]} 

GOAL:
- VALIDATE coordinates and pin count against the real-world component datasheet.
- RENAME pins to match official datasheet labels.
- ADD an 'interactive' object to the JSON mapping 'action' to 'svgId' (e.g., {{"type": "led", "id": "led_glow_part"}}).
- IMPROVE the component 'label' to be the full, official part number.
- Return ONLY the improved JSON. No chat, no markdown blocks.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        # Clean response (remove markdown code blocks if present)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
        
        improved_json = json.loads(text.strip())
        return improved_json
    except Exception as e:
        print(f"  !! AI Refinement failed: {e}")
        return draft_json

def parse_dimension(dim_str):
    dim_str = str(dim_str).strip().lower()
    if not dim_str:
        return 0.0
    
    # Extract number
    match = re.match(r'([0-9\.]+)(in|mm|cm|px)?', dim_str)
    if not match:
        return 0.0
        
    val = float(match.group(1))
    unit = match.group(2)
    
    if unit == 'in':
        return val * 72.0
    elif unit == 'mm':
        return val * (72.0 / 25.4)
    elif unit == 'cm':
        return val * (72.0 / 2.54)
    else: # px or unitless
        return val

def import_fritzing_part(fzp_path, svg_path, component_folder_name, use_ai=False):
    # Conversion Factor: 72 DPI (Fritzing) to 80 Units Per Inch (AURA)
    # AURA is 1u = 0.3175mm (12.5 mils). 80u = 1 inch.
    SCALE = 80.0 / 72.0

    # Parse XML
    try:
        with open(fzp_path, 'r', encoding='utf-8') as f:
            fzp_content = f.read()
        tree = ET.fromstring(fzp_content)
        root = tree
    except Exception as e:
        print(f"Error parsing FZP {fzp_path}: {e}")
        return None

    module_id = root.attrib.get('moduleId', component_folder_name)
    title_el = root.find('title')
    title = title_el.text if title_el is not None else component_folder_name

    # Try to extract a category from tags
    tags_el = root.find('tags')
    category = "Other"
    if tags_el is not None:
        tags = [t.text.lower() for t in tags_el.findall('tag') if t.text]
        if any('led' in t or 'display' in t or 'lcd' in t or 'oled' in t or 'segment' in t or 'matrix' in t for t in tags):
            category = "Optoelectronics"
        elif any('resistor' in t or 'capacitor' in t for t in tags):
            category = "Passive"
        elif any('microcontroller' in t or 'arduino' in t for t in tags):
            category = "Microcontroller"

    # Parse SVG for coordinates
    try:
        svg_tree = ET.parse(svg_path)
        svg_root = svg_tree.getroot()
    except Exception as e:
        print(f"Error parsing SVG {svg_path}: {e}")
        return None

    # Find SVG dimensions
    width_attr = svg_root.attrib.get('width', '0')
    height_attr = svg_root.attrib.get('height', '0')

    width_px = parse_dimension(width_attr)
    height_px = parse_dimension(height_attr)

    # Fallback to viewBox if width/height is missing or 0
    if width_px == 0 or height_px == 0:
        viewbox = svg_root.attrib.get('viewBox')
        if viewbox:
            parts = viewbox.replace(',', ' ').split()
            if len(parts) >= 4:
                width_px = float(parts[2])
                height_px = float(parts[3])

    # If still 0, provide a safe default to prevent disappearing components
    if width_px == 0: width_px = 100
    if height_px == 0: height_px = 100

    uW = round(width_px * SCALE)
    uH = round(height_px * SCALE)

    # We set origin to center
    originX = uW / 2
    originY = uH / 2

    # Map connectors
    pins = []
    connectors = root.find('connectors')

    if connectors is not None:
        for conn in connectors.findall('connector'):
            conn_id = conn.attrib.get('id')
            name = conn.attrib.get('name', conn_id)

            # Look for explicit breadboard SVG ID in the FZP if available
            explicit_svg_id = None
            bb_view = conn.find(".//breadboardView/p")
            if bb_view is not None:
                explicit_svg_id = bb_view.attrib.get('svgId')

            # Search targets for the pin in the SVG
            search_ids = [
                explicit_svg_id,
                f"{conn_id}pin", 
                f"{conn_id}pad", 
                f"{conn_id}leg",
                f"{conn_id}terminal"
            ]
            search_ids = [s for s in search_ids if s] # Remove Nones

            found_el = None
            for el in svg_root.iter():
                el_id = el.attrib.get('id')
                if el_id in search_ids:
                    found_el = el
                    # Prefer 'pin' or explicit over 'leg' if multiple match
                    if 'pin' in (el_id or '') or el_id == explicit_svg_id:
                        break

            if found_el is not None:
                # Get center of circle, rect, or path
                cx = float(found_el.attrib.get('cx', found_el.attrib.get('x', 0)))
                cy = float(found_el.attrib.get('cy', found_el.attrib.get('y', 0)))

                # If it was a rect, add half width/height to get center
                if 'width' in found_el.attrib and 'cx' not in found_el.attrib:
                    cx += float(found_el.attrib.get('width', 0)) / 2
                if 'height' in found_el.attrib and 'cy' not in found_el.attrib:
                    cy += float(found_el.attrib.get('height', 0)) / 2

                # Convert to AURA units (relative to center)
                aura_x = (cx * SCALE) - originX
                aura_y = originY - (cy * SCALE)

                pins.append({
                    "id": conn_id,
                    "uX": round(aura_x),
                    "uY": round(aura_y),
                    "label": name
                })

    svg_filename = os.path.basename(svg_path)

    draft_result = {
        "type": component_folder_name,
        "label": title,
        "category": category,
        "views": {
            "breadboard": f"assets/{svg_filename}",
            "schematic": None,
            "pcb": None
        },
        "uW": uW,
        "uH": uH,
        "originX": originX,
        "originY": originY,
        "pins": pins
    }

    if use_ai and AI_ENABLED:
        print(f"  -> Applying AI Aurification for {title}...")
        return aurify_with_ai(draft_result, fzp_content)
    
    return draft_result

def run_bulk_import(use_ai=False):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parts_dir = os.path.join(base_dir, 'parts_library')

    print(f"Scanning parts library (AI: {'ON' if use_ai and AI_ENABLED else 'OFF'})...")

    for folder_name in os.listdir(parts_dir):
        folder_path = os.path.join(parts_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        fzp_files = glob.glob(os.path.join(folder_path, 'fzp', '*.fzp'))
        svg_files = glob.glob(os.path.join(folder_path, 'assets', '*.svg'))

        # Only process if it has exactly one of each
        if len(fzp_files) == 1 and len(svg_files) >= 1:
            manifest_path = os.path.join(folder_path, 'manifest.json')
            print(f"Processing: {folder_name}")
            manifest_data = import_fritzing_part(fzp_files[0], svg_files[0], folder_name, use_ai=use_ai)

            if manifest_data:
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest_data, f, indent=2)
                print(f"  -> Updated manifest.json")
            else:
                print(f"  -> Failed to generate data")

if __name__ == "__main__":
    import sys
    # Use --ai flag to enable Gemini refinement
    ai_flag = "--ai" in sys.argv
    run_bulk_import(use_ai=ai_flag)
