def generate_breadboard_svg() -> str:
    """Generates an SVG for a standard half-size breadboard (400 points)."""
    # 1u = 0.3175mm. Standard pitch is 8u (2.54mm).
    u = 1.0
    pitch = 8 * u
    
    cols = 30
    rows_half = 5
    
    width = (cols + 4) * pitch
    height = (rows_half * 2 + 6) * pitch
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" version="1.2" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'''
    
    # Body
    svg += f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fdfdfd" rx="{4*u}" stroke="#dddddd" stroke-width="1"/>'
    
    # Center divider
    center_y = height / 2
    svg += f'<rect x="{2*pitch}" y="{center_y - 1*u}" width="{cols*pitch}" height="{2*u}" fill="#e0e0e0" />'
    
    # Pins (Power rails - simplified for now, just terminal rows)
    # We will just generate the main terminal strips (A-E and F-J)
    
    pin_id = 0
    
    # Top Half (A-E)
    start_y_top = center_y - (5 * pitch)
    for col in range(cols):
        cx = (col + 2.5) * pitch
        for row in range(5):
            cy = start_y_top + (row * pitch)
            svg += f'<rect id="pin_{pin_id}" x="{cx - 1.5*u}" y="{cy - 1.5*u}" width="{3*u}" height="{3*u}" fill="#222222" rx="0.5"/>'
            pin_id += 1
            
    # Bottom Half (F-J)
    start_y_bot = center_y + (1 * pitch)
    for col in range(cols):
        cx = (col + 2.5) * pitch
        for row in range(5):
            cy = start_y_bot + (row * pitch)
            svg += f'<rect id="pin_{pin_id}" x="{cx - 1.5*u}" y="{cy - 1.5*u}" width="{3*u}" height="{3*u}" fill="#222222" rx="0.5"/>'
            pin_id += 1
            
    # Add text labels (1, 5, 10...)
    for col in range(0, cols, 5):
        cx = (col + 2.5) * pitch
        svg += f'<text x="{cx}" y="{start_y_top - 2*u}" fill="#888888" font-family="monospace" font-size="{3*u}" text-anchor="middle">{col+1}</text>'
        svg += f'<text x="{cx}" y="{start_y_bot + 5*pitch + 3*u}" fill="#888888" font-family="monospace" font-size="{3*u}" text-anchor="middle">{col+1}</text>'

    svg += '</svg>'
    return svg

def get_breadboard_pins():
    """Returns the pin metadata for the breadboard."""
    u = 1.0
    pitch = 8 * u
    cols = 30
    width = (cols + 4) * pitch
    height = (5 * 2 + 6) * pitch
    center_y = height / 2
    originX = width / 2
    originY = height / 2
    
    pins = []
    pin_id = 0
    
    start_y_top = center_y - (5 * pitch)
    for col in range(cols):
        cx = (col + 2.5) * pitch
        for row in range(5):
            cy = start_y_top + (row * pitch)
            pins.append({"id": f"pin_{pin_id}", "uX": round(cx - originX), "uY": round(originY - cy), "label": f"{chr(65+row)}{col+1}"})
            pin_id += 1
            
    start_y_bot = center_y + (1 * pitch)
    for col in range(cols):
        cx = (col + 2.5) * pitch
        for row in range(5):
            cy = start_y_bot + (row * pitch)
            pins.append({"id": f"pin_{pin_id}", "uX": round(cx - originX), "uY": round(originY - cy), "label": f"{chr(70+row)}{col+1}"})
            pin_id += 1
            
    return {"uW": round(width), "uH": round(height), "originX": round(originX), "originY": round(originY), "pins": pins}
