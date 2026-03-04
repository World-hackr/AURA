from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.engines.calculation_engine import calculate_led_resistor
from app.engines.ic_generator import generate_dip_ic_svg
from app.engines.breadboard_generator import generate_breadboard_svg, get_breadboard_pins
import json
import os
import math
import xml.etree.ElementTree as ET
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
parts_library_path = os.path.join(BASE_DIR, "parts_library")

class NoCacheStaticFiles(StaticFiles):
    def is_not_modified(self, response_headers, request_headers) -> bool: return False
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

app.mount("/symbols", NoCacheStaticFiles(directory=parts_library_path), name="symbols")

@app.get("/api/components")
def get_components():
    all_parts = []
    for part_dir in os.listdir(parts_library_path):
        manifest_path = os.path.join(parts_library_path, part_dir, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r") as f:
                part_data = json.load(f)
                
                if part_data.get("type") == "ic_dynamic":
                    part_data["views"]["breadboard"] = "dynamic"
                elif part_data.get("type") == "breadboard_half":
                    part_data["views"]["breadboard"] = "dynamic"
                    # Inject dynamic pins and dimensions
                    bb_data = get_breadboard_pins()
                    part_data.update(bb_data)
                elif "views" in part_data:
                    for v in part_data["views"]:
                        if part_data["views"][v]: part_data["views"][v] = f"{part_dir}/{part_data['views'][v]}"
                all_parts.append(part_data)
    return all_parts

def get_resistor_colors(resistance: float, is_5band: bool = False):
    digit_colors = {0:"#000000", 1:"#663300", 2:"#FF0000", 3:"#FF6600", 4:"#FFFF00", 5:"#00CC00", 6:"#0000FF", 7:"#CC00CC", 8:"#808080", 9:"#FFFFFF"}
    multiplier_colors = {-2:"#C0C0C0", -1:"#CFB53B", 0:"#000000", 1:"#663300", 2:"#FF0000", 3:"#FF6600", 4:"#FFFF00", 5:"#00CC00", 6:"#0000FF", 7:"#CC00CC", 8:"#808080", 9:"#FFFFFF"}
    if resistance <= 0: return (digit_colors[0], digit_colors[0], multiplier_colors[0]) if not is_5band else (digit_colors[0], digit_colors[0], digit_colors[0], multiplier_colors[0])
    exp = math.floor(math.log10(resistance)) - (2 if is_5band else 1)
    sig_figs = round(resistance / (10**exp))
    if sig_figs >= (1000 if is_5band else 100): sig_figs //= 10; exp += 1
    if is_5band: return digit_colors[sig_figs//100], digit_colors[(sig_figs//10)%10], digit_colors[sig_figs%10], multiplier_colors.get(exp, "#000")
    return digit_colors[sig_figs//10], digit_colors[sig_figs%10], multiplier_colors.get(exp, "#000")

def parse_resistance(val_str: str) -> float:
    val_str = val_str.replace('Ω', '').replace('ohm', '').replace('Ohm', '').replace(' ', '')
    val_str = val_str.lower()
    for unit, mult in [('g', 1e9), ('m', 1e6), ('k', 1e3)]:
        if unit in val_str:
            if unit != val_str[-1]: return float(val_str.replace(unit, '.')) * mult
            return float(val_str.replace(unit, '')) * mult
    try: return float(val_str)
    except: return 0.0

@app.get("/api/dynamic_svg/{comp_type}")
def get_dynamic_svg(comp_type: str, request: Request):
    query_params = dict(request.query_params)
    
    # --- DYNAMIC GENERATORS ---
    if comp_type == "ic_dynamic":
        try: pins = int(query_params.get("pins", 8))
        except: pins = 8
        label = query_params.get("ic_label", "NE555")
        svg_text = generate_dip_ic_svg(pins, label)
        return Response(content=svg_text, media_type="image/svg+xml")
        
    if comp_type == "breadboard_half":
        svg_text = generate_breadboard_svg()
        return Response(content=svg_text, media_type="image/svg+xml")

    folder_path = os.path.join(parts_library_path, comp_type)
    manifest_path = os.path.join(folder_path, "manifest.json")
    if not os.path.exists(manifest_path): return Response(status_code=404)
    with open(manifest_path, 'r') as f: manifest = json.load(f)
    if manifest['views']['breadboard'] == "dynamic": return Response(status_code=404)
    
    svg_abs_path = os.path.join(folder_path, "assets", os.path.basename(manifest['views']['breadboard']))
    
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    tree = ET.parse(svg_abs_path)
    root = tree.getroot()

    # --- GENERALIZED DYNAMIC ENGINE ---
    interactive_rules = manifest.get('interactive', [])
    if isinstance(interactive_rules, dict): # Handle legacy single-object format
        interactive_rules = [interactive_rules]

    for rule in interactive_rules:
        rid = rule.get('id')
        rtype = rule.get('type')
        prop_name = rule.get('property')
        prop_val = query_params.get(prop_name)

        if not rtype: continue

        # Find target element(s) - Use substring match for robustness with Fritzing IDs
        targets = []
        for el in root.iter():
            eid = el.attrib.get('id', '')
            # Case-insensitive substring match for flexibility
            if rid and rid.lower() in eid.lower():
                targets.append(el)
            elif rtype == 'resistor_bands' and 'band' in eid.lower():
                targets.append(el)
        
        if not targets and rtype != 'resistor_bands': continue

        if rtype == 'resistor_bands':
            try:
                r_val = parse_resistance(query_params.get("resistance", "0") + query_params.get("unit", ""))
                is_5 = "5band" in comp_type
                colors = get_resistor_colors(r_val, is_5)
                tol_map = {"Gold": "#CFB53B", "Silver": "#C0C0C0", "Brown": "#663300", "Red": "#FF0000", "Green": "#00CC00", "Blue": "#0000FF", "Violet": "#CC00CC"}
                tol_hex = tol_map.get(query_params.get("tolerance"), "#CFB53B")

                for el in targets:
                    eid = el.attrib.get('id', '').lower()
                    c = None
                    if 'gold_band' in eid or 'tolerance' in eid: c = tol_hex
                    elif is_5:
                        if 'band_1' in eid: c = colors[0]
                        elif 'band_2' in eid: c = colors[1]
                        elif 'band_3' in eid: c = colors[2]
                        elif 'band_rd' in eid or 'multiplier' in eid: c = colors[3]
                    else:
                        if 'band_1' in eid: c = colors[0]
                        elif 'band_2' in eid: c = colors[1]
                        elif 'band_rd' in eid or 'band_3' in eid or 'multiplier' in eid: c = colors[2]
                    
                    if c:
                        el.set('fill', c)
                        if 'style' in el.attrib:
                            el.set('style', re.sub(r'fill:[^;]+', f'fill:{c}', el.attrib['style']))
            except Exception as e:
                print(f"Resistor coloring error: {e}")

        elif rtype == 'rotate':
            try:
                val = float(prop_val or 0)
                r_min, r_max = rule.get('range', [0, 100])
                a_min, a_max = rule.get('angleRange', [0, 360])
                
                ratio = (val - r_min) / (r_max - r_min) if (r_max - r_min) != 0 else 0
                angle = a_min + ratio * (a_max - a_min)
                ox, oy = rule.get('origin', [manifest.get('originX', 0), manifest.get('originY', 0)])
                
                for el in targets:
                    # We only rotate the *topmost* element that matches the ID (usually the group)
                    # to avoid double rotations if sub-elements also match the substring.
                    # But for now, rotating everything is safer if they are separate.
                    existing_transform = el.attrib.get('transform', '')
                    new_transform = f"rotate({angle}, {ox}, {oy})"
                    if existing_transform:
                        el.set('transform', f"{new_transform} {existing_transform}")
                    else:
                        el.set('transform', new_transform)
            except Exception as e:
                print(f"Rotation error: {e}")

        elif rtype == 'color':
            color_map = rule.get('map', {})
            target_color = color_map.get(prop_val, prop_val)
            if target_color:
                for el in targets:
                    el.set('fill', target_color)
                    if 'style' in el.attrib:
                        el.set('style', re.sub(r'fill:[^;]+', f'fill:{target_color}', el.attrib['style']))

        elif rtype == 'opacity':
            try:
                val = float(prop_val or 0)
                r_min, r_max = rule.get('range', [0, 100])
                o_min, o_max = rule.get('opacityRange', [0.1, 1.0])
                ratio = (val - r_min) / (r_max - r_min) if (r_max - r_min) != 0 else 0
                opacity = round(o_min + ratio * (o_max - o_min), 3)
                
                for el in targets:
                    el.set('fill-opacity', str(opacity))
                    # Also set opacity attribute for broader compatibility
                    el.set('opacity', str(opacity))
                    if 'style' in el.attrib:
                        s = el.attrib['style']
                        s = re.sub(r'fill-opacity:[^;]+', f'fill-opacity:{opacity}', s)
                        s = re.sub(r'opacity:[^;]+', f'opacity:{opacity}', s)
                        el.set('style', s)
            except Exception as e:
                print(f"Opacity error: {e}")

    # --- LEGACY / HARDCODED FALLBACKS (To be removed once all manifests are updated) ---
    if not interactive_rules:
        if "resistor" in comp_type:
            r_val = parse_resistance(query_params.get("resistance", "0") + query_params.get("unit", ""))
            is_5 = "5band" in comp_type
            colors = get_resistor_colors(r_val, is_5)
            tol_map = {"Gold": "#CFB53B", "Silver": "#C0C0C0", "Brown": "#663300", "Red": "#FF0000", "Green": "#00CC00", "Blue": "#0000FF", "Violet": "#CC00CC"}
            tol_hex = tol_map.get(query_params.get("tolerance"), "#CFB53B")

            for el in root.iter():
                eid = el.attrib.get('id', '').lower()
                c = None
                if 'gold_band' in eid or 'tolerance' in eid: c = tol_hex
                elif is_5:
                    if 'band_1' in eid: c = colors[0]
                    elif 'band_2' in eid: c = colors[1]
                    elif 'band_3' in eid: c = colors[2]
                    elif 'band_rd' in eid or 'multiplier' in eid: c = colors[3]
                else:
                    if 'band_1' in eid: c = colors[0]
                    elif 'band_2' in eid: c = colors[1]
                    elif 'band_rd' in eid or 'band_3' in eid or 'multiplier' in eid: c = colors[2]
                
                if c:
                    el.set('fill', c)
                    if 'style' in el.attrib:
                        el.set('style', re.sub(r'fill:[^;]+', f'fill:{c}', el.attrib['style']))

        elif "led" in comp_type and "arduino" not in comp_type:
            try: brightness = max(0, min(100, float(query_params.get("brightness", "0")))) / 100.0
            except: brightness = 0.0
            
            target = {"Red": "#FF0000", "Green": "#00FF00", "Blue": "#0000FF", "Yellow": "#FFFF00", "White": "#FFFFFF"}.get(query_params.get("color"), "#FF0000")
            op_val = round(0.1 + 0.9 * brightness, 3)
            
            for el in root.iter():
                eid = el.attrib.get('id', '').lower()
                if "led_glow" in eid or "body" in eid or "lens" in eid:
                    el.set('fill', target)
                    el.set('fill-opacity', str(op_val))
                    if 'style' in el.attrib: 
                        s = re.sub(r'fill:[^;]+', f'fill:{target}', el.attrib['style'])
                        s = re.sub(r'fill-opacity:[^;]+', f'fill-opacity:{op_val}', s)
                        el.set('style', s)

    # --- MODULE INDICATOR LOGIC (e.g. Arduino PWR/L LEDs) ---
    if "arduino" in comp_type:
        b_param = query_params.get("brightness", "100")
        try: b_val = max(0, min(100, float(b_param))) / 100.0
        except: b_val = 1.0
        op = round(0.1 + 0.9 * b_val, 3)
        
        for el in root.iter():
            eid = (el.attrib.get('id') or "").lower()
            if eid.startswith("led_"):
                # Force color based on component type
                m_color = "#00FF00" if "pwr" in eid else "#FFFF00"
                el.set('fill', m_color)
                el.set('fill-opacity', str(op))
                # CRITICAL: Strip internal styles that might be locking a "corner" to a static color
                if 'style' in el.attrib:
                    s = el.attrib['style']
                    s = re.sub(r'fill:[^;]+', f'fill:{m_color}', s)
                    s = re.sub(r'fill-opacity:[^;]+', f'fill-opacity:{op}', s)
                    el.set('style', s)

    return Response(content=ET.tostring(root, encoding='utf-8', method='xml', xml_declaration=True), media_type="image/svg+xml")

@app.get("/calculate_led_resistor")
def led_resistor(vs: float, vf: float, current: float):
    return {"resistance": calculate_led_resistor(vs, vf, current), "unit": "ohms"}