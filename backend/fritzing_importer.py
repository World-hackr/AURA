import xml.etree.ElementTree as ET
import json
import os

def import_fritzing_part(fzp_path, svg_path):
    # Conversion Factor: 72 DPI (Fritzing) to 80 Units Per Inch (AURA)
    SCALE = 80.0 / 72.0

    # Parse XML
    tree = ET.parse(fzp_path)
    root = tree.getroot()
    
    module_id = root.attrib.get('moduleId')
    title = root.find('title').text
    
    # Parse SVG for coordinates
    svg_tree = ET.parse(svg_path)
    svg_root = svg_tree.getroot()
    
    # Find SVG dimensions
    # Stripping 'px' if present
    width_px = float(svg_root.attrib.get('width').replace('px',''))
    height_px = float(svg_root.attrib.get('height').replace('px',''))
    
    uW = round(width_px * SCALE)
    uH = round(height_px * SCALE)
    
    # We set origin to center
    originX = uW / 2
    originY = uH / 2
    
    # Map connectors
    pins = []
    connectors = root.find('connectors')
    
    # Namespace handling for SVG
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    
    for conn in connectors.findall('connector'):
        conn_id = conn.attrib.get('id')
        name = conn.attrib.get('name')
        
        # Find the corresponding SVG element
        # Fritzing usually uses id='connectorIDpin' or id='connectorIDpad'
        svg_id = f"{conn_id}pin"
        
        # Search for the element in SVG
        # This is a simplified search
        found_el = None
        for el in svg_root.iter():
            if el.attrib.get('id') == svg_id:
                found_el = el
                break
        
        if found_el is not None:
            # Get center of circle or rect
            cx = float(found_el.attrib.get('cx', 0))
            cy = float(found_el.attrib.get('cy', 0))
            
            # Convert to AURA units (relative to center)
            # AURA Y is up, SVG Y is down
            aura_x = (cx * SCALE) - originX
            aura_y = originY - (cy * SCALE)
            
            pins.append({
                "id": conn_id,
                "uX": round(aura_x),
                "uY": round(aura_y),
                "label": name
            })

    result = {
        "type": module_id.lower().replace('-', '_'),
        "label": title,
        "uW": uW,
        "uH": uH,
        "originX": originX,
        "originY": originY,
        "pins": pins
    }
    
    return result

if __name__ == "__main__":
    # This is a template for how you'll use it
    print("AURA Fritzing Importer Ready.")
