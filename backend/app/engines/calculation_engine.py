def calculate_led_resistor(vs, vf, current):
    """
    Calculate LED resistor value
    
    vs = supply voltage (V)
    vf = LED forward voltage (V)
    current = current (A)
    """
    
    resistance = (vs - vf) / current
    
    return resistance