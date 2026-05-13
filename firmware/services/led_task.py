import uasyncio as asyncio
from machine import Pin
import neopixel
from logger import Logger

# ---- Global variables ----
import shared_variables as var

# breathing table, values 1..100
BREATH_TABLE = [
    0,0,0,0,0,1,1,1,2,2,3,4,5,6,7,8,
    10,11,13,15,17,19,22,24,27,30,33,36,39,42,46,49,
    53,56,60,63,67,70,74,77,80,83,86,89,91,93,95,96,
    97,98,99,99,100,100,100,100,100,99,99,98,97,96,95,93,
    91,89,86,83,80,77,74,70,67,63,60,56,53,49,46,42,
    39,36,33,30,27,24,22,19,17,15,13,11,10,8,7,6,
    5,4,3,2,2,1,1,1,0,0,0,0
]

# global / persistent
v_breath_filt = 0.0

def smooth_breath(v):
    global v_breath_filt

    # Preserve true endpoints immediately
    if v <= 0:
        v_breath_filt = 0.0
        return 0.0

    if v >= 100:
        v_breath_filt = 100.0
        return 100.0

    # Light smoothing
    alpha = 0.35   # higher = faster, lower = smoother
    v_breath_filt += alpha * (v - v_breath_filt)

    return v_breath_filt

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
    pin = Pin(43, Pin.OUT)
    np = neopixel.NeoPixel(pin, 18)

    phase = 0
    v_breath = 0
    dir = 1
    idx = 0
    #Run
    while True:
        # Welcome screen is not registered as normal screens so at startup len is 0
        if len(var.screen_names) > 0:
            # Breathing animation on CO2 screens, LED color only depends on CO2 level
            if not var.selected_alt and not var.selected_game and var.screen_names[var.current_idx] in ["CO2", "CO2 chart"]:
                value = var.sensor_data.co2_scd41
                if value < 1000:
                    h = 120
                elif value < 1500:
                    h = 48
                else:
                    h = 0
                    
                s = 100
                
                # LUT sinusoidal breathing animation
                v_breath = BREATH_TABLE[idx]
                idx += 1
                if idx >= len(BREATH_TABLE):
                    idx = 0
                    
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
                
                v_breath_scaled = smooth_breath(v_breath_scaled)
                rgb = convert_hsv2rgb(h, s, v_breath_scaled)
                for i in range(0, len(np)):
                    np[i] = rgb
                    
                np.write() # write data to all pixels
            
            # Breathing animation on multi-sensor screen where worst sensor reading decides the color
            elif not var.selected_alt and not var.selected_game and var.screen_names[var.current_idx] in ["Sensors"]:
                
                if var.led_request_co2 == "Red" or var.led_request_temp == "Red" or var.led_request_hum == "Red":
                    h = 0
                elif var.led_request_co2 == "Yellow" or var.led_request_temp == "Yellow" or var.led_request_hum == "Yellow":
                    h = 48
                elif var.led_request_co2 == "Blue" or var.led_request_temp == "Blue" or var.led_request_hum == "Blue":
                    h = 210
                else:
                    h = 120
                                   
                s = 100
                
                # LUT sinusoidal breathing animation
                v_breath = BREATH_TABLE[idx]
                idx += 1
                if idx >= len(BREATH_TABLE):
                    idx = 0
                    
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
                    
                v_breath_scaled = smooth_breath(v_breath_scaled)
                rgb = convert_hsv2rgb(h, s, v_breath_scaled)
                for i in range(0, len(np)):
                    np[i] = rgb
                    
                np.write() # write data to all pixels
                
            # On roll and snake screens rainbow animation is too slow
            elif var.selected_alt and not var.selected_game and var.screen_names_alt[var.current_idx_alt] in ["Roll"] or \
                 not var.selected_alt and var.selected_game and var.screen_names_game[var.current_idx_game] in ["Snake"]:
                
                for i in range(0, len(np)):
                    np[i] = (20, 20, 20)
                np.write() # write data to all pixels
                
            # Rotation rainbow animation as default
            else:
                for i in range(0, len(np)):
                    h = phase + i*360.0 / (len(np)-0)
                    s = 100
                    v = 20
                    
                    np[i] = convert_hsv2rgb(h, s, v)
                
                np.write() # write data to all pixels
                phase += 10
                
        # Only at startup when there are no valid screens registered        
        else:
            for i in range(0, len(np)):
                np[i] = (30, 30, 100)
            np.write() # write data to all pixels

        await asyncio.sleep(period)
        
        
