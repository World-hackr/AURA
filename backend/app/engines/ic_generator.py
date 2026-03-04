def generate_dip_ic_svg(pins: int, label: str) -> str:
    """Generates an SVG for a standard DIP IC."""
    if pins % 2 != 0: pins += 1 # Must be even
    if pins < 4: pins = 4
    
    # 1u = 0.3175mm. Standard DIP pitch is 8u (2.54mm).
    # Width of standard narrow DIP is 300 mils = ~24u
    
    u = 1.0 # Scale multiplier
    pitch = 8 * u
    width = 24 * u
    
    pins_per_side = pins // 2
    height = (pins_per_side * pitch) + (4 * u)
    
    # Body rect
    body_x = 4 * u
    body_y = 2 * u
    body_w = width - (8 * u)
    body_h = height - (4 * u)
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" version="1.2" viewBox="0 0 {width} {height}" width="{width}" height="{height}">'''
    
    # Pins
    for i in range(pins_per_side):
        # Left side (1 to N/2)
        py = body_y + (i * pitch) + (2 * u)
        svg += f'<rect id="pin_{i+1}" x="0" y="{py - 1*u}" width="{4*u}" height="{2*u}" fill="#C0C0C0" />'
        # Right side (N to N/2 + 1)
        svg += f'<rect id="pin_{pins-i}" x="{width - 4*u}" y="{py - 1*u}" width="{4*u}" height="{2*u}" fill="#C0C0C0" />'
    
    # Body
    svg += f'<rect x="{body_x}" y="{body_y}" width="{body_w}" height="{body_h}" fill="#222222" rx="1" />'
    
    # Notch (Pin 1 indicator)
    notch_r = 2 * u
    svg += f'<path d="M {body_x + body_w/2 - notch_r} {body_y} a {notch_r} {notch_r} 0 0 0 {notch_r*2} 0" fill="#222222" stroke="#111111" stroke-width="0.5"/>'
    
    # Pin 1 Dot
    svg += f'<circle cx="{body_x + 2*u}" cy="{body_y + 2*u}" r="{0.8*u}" fill="#111111" />'
    
    # Label
    svg += f'<text x="{body_x + body_w/2}" y="{body_y + body_h/2}" fill="#FFFFFF" font-family="monospace" font-size="{4*u}" text-anchor="middle" dominant-baseline="middle" transform="rotate(-90 {body_x + body_w/2} {body_y + body_h/2})">{label}</text>'
    
    svg += '</svg>'
    return svg
