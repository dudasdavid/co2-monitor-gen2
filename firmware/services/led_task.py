import uasyncio as asyncio
from machine import Pin
import neopixel

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
    #Init
    pin = Pin(44, Pin.OUT)
    np = neopixel.NeoPixel(pin, 20)

    phase = 0
    #Run
    while True:
        
        for i in range(0, len(np)):
            h = phase + i*360.0 / (len(np)-0)
            s = 100
            v = 20
            
            np[i] = convert_hsv2rgb(h, s, v)
        
        
        
        np.write() # write data to all pixels
        phase += 10

        await asyncio.sleep(period)
        
        
