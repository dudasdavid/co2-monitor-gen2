import uasyncio as asyncio
from machine import Pin
import neopixel
from logger import Logger

# ---- Global variables ----
import shared_variables as var

def convert_hsv2rgb(h,s,v):
    """
    Convert HSV (Hue 0–360, Saturation 0–100, Value 0–100)
    to RGB (each 0–255)
    """
    s /= 100.0
    v /= 100.0

    if s == 0:
        r = g = b = int(v * 255)
        return (r, g, b)

    h = h % 360
    h_div = h / 60
    i = int(h_div)
    f = h_div - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))

    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q

    return (int(r * 255), int(g * 255), int(b * 255))

async def led_task(period = 1.0):
    
    log = Logger("led", debug_enabled=False)
    
    #Init
    pin = Pin(44, Pin.OUT)
    np = neopixel.NeoPixel(pin, 18)

    phase = 0
    v_breath = 0
    dir = 1
    #Run
    while True:
        
        
        if var.screen_names[var.current_idx] in ["CO2", "CO2 chart"]:
            value = var.sensor_data.co2_scd41
            if value < 1000:
                h = 120
            elif value < 1500:
                h = 48
            else:
                h = 0
                
            s = 100
            
            
            v_breath += dir * 1
            if v_breath > 100:
                v_breath = 100
                dir = -1
            elif v_breath < 1:
                v_breath = 1
                dir = 1
                
            # Ambient lux based LED ring intensity calculation
            lux = var.sensor_data.lux_veml7700
            # No animation on the lowest light intensity
            if lux < 5:
                v_breath_scaled = 0.5
            else:
                # v_scaled can be between /3 to /10 based on lux
                lux_min = 5.0
                lux_max = 100.0

                # clamp lux into range
                lux_clamped = max(lux_min, min(lux, lux_max))

                # normalize 0..1
                t = (lux_clamped - lux_min) / (lux_max - lux_min)

                # scale goes from 1/10 -> 1/3
                scale = (1/10) + t * ((1/3) - (1/10))

                v_breath_scaled = v_breath * scale
            
            # To avoid low yellow turning to red
            if v_breath_scaled < 0.5:
                v_breath_scaled = 0.5
                
            # In pitch black turn off LEDs completely
            if var.sensor_data.lux_veml7700 < 1:
                v_breath_scaled = 0
            
            rgb = convert_hsv2rgb(h, s, v_breath_scaled)
            for i in range(0, len(np)):
                np[i] = rgb
                
            np.write() # write data to all pixels
        
        else:
            for i in range(0, len(np)):
                h = phase + i*360.0 / (len(np)-0)
                s = 100
                v = 20
                
                np[i] = convert_hsv2rgb(h, s, v)
            
            
            
            np.write() # write data to all pixels
            phase += 10

        await asyncio.sleep(period)
        
        
