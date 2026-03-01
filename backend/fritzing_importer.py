import xml.etree.ElementTree as ET
import json
import os
import glob
import re

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

def import_fritzing_part(fzp_path, svg_path, component_folder_name):
    # Conversion Factor: 72 DPI (Fritzing) to 80 Units Per Inch (AURA)
    # AURA is 1u = 0.3175mm (12.5 mils). 80u = 1 inch.
    SCALE = 80.0 / 72.0

    # Parse XML
    try:
        tree = ET.parse(fzp_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing FZP {fzp_path}: {e}")
        return None

    module_id = root.attrib.get('moduleId', component_folder_name)
    title_el = root.find('title')
    title = title_el.text if title_el is not None else component_folder_name

    # Try to extract a category from tags
    tags_el = root.find('tags')
    category = "Uncategorized"
    if tags_el is not None:
        tags = [t.text.lower() for t in tags_el.findall('tag') if t.text]
        if any('led' in t or 'display' in t or 'lcd' in t or 'oled' in t or 'segment' in t or 'matrix' in t for t in tags):
            category = "Optoelectronics"
        elif any('resistor' in t or 'capacitor' in t for t in tags):
            category = "Passives"
        elif any('microcontroller' in t or 'arduino' in t for t in tags):
            category = "MCU"

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
                    if 'pin' in el_id or el_id == explicit_svg_id:
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

    result = {
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

    return result

def run_bulk_import():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parts_dir = os.path.join(base_dir, 'parts_library')

    print("Scanning parts library for FZP/SVG pairs...")

    for folder_name in os.listdir(parts_dir):
        folder_path = os.path.join(parts_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        fzp_files = glob.glob(os.path.join(folder_path, 'fzp', '*.fzp'))
        svg_files = glob.glob(os.path.join(folder_path, 'assets', '*.svg'))

        # Only process if it has exactly one of each
        if len(fzp_files) == 1 and len(svg_files) >= 1:
            manifest_path = os.path.join(folder_path, 'manifest.json')
            print(f"Generating manifest for: {folder_name}")
            manifest_data = import_fritzing_part(fzp_files[0], svg_files[0], folder_name)

            if manifest_data:
                with open(manifest_path, 'w') as f:
                    json.dump(manifest_data, f, indent=2)
                print(f"  -> Updated manifest.json")
            else:
                print(f"  -> Failed to generate data")

if __name__ == "__main__":
    run_bulk_import()
