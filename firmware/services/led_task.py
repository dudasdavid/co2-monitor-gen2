import uasyncio as asyncio
from micropython import const
from machine import Pin
import neopixel
from logger import Logger

# ---- Global variables ----
import shared_variables as var

# ---- Constants -----------
LED_PIN   = const(43)
LED_COUNT = const(18)

H_GREEN   = const(120)
H_YELLOW  = const(48)
H_RED     = const(0)
H_BLUE    = const(210)

SAT_FULL  = const(100)

RAINBOW_VALUE = const(20)
STATIC_VALUE  = (20, 20, 20)
STARTUP_VALUE = (30, 30, 100)

LUX_OFF = const(1.0)
LUX_LOW = const(5.0)
LUX_MAX = const(100.0)

BREATH_MIN_VISIBLE  = 0.5
BREATH_SCALE_DARK   = 1 / 10
BREATH_SCALE_BRIGHT = 1 / 3

SMOOTH_ALPHA = const(0.35)

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

# ---- Persistent animation state ----
v_breath_filt = 0.0

# ---- Helper functions --------------
def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x

def fill(np, rgb):
    for i in range(len(np)):
        np[i] = rgb
    np.write()

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

# ---- Screen state helpers ----------------
def normal_screen_active(name):
    return (
        not var.selected_alt and
        not var.selected_game and
        len(var.screen_names) > 0 and
        var.screen_names[var.current_idx] == name
    )

def normal_screen_in(names):
    return (
        not var.selected_alt and
        not var.selected_game and
        len(var.screen_names) > 0 and
        var.screen_names[var.current_idx] in names
    )

def roll_or_snake_active():
    roll_active = (
        var.selected_alt and
        not var.selected_game and
        var.screen_names_alt[var.current_idx_alt] in ["Roll"]
    )

    snake_active = (
        not var.selected_alt and
        var.selected_game and
        var.screen_names_game[var.current_idx_game] in ["Snake"]
    )

    return roll_active or snake_active

# ---- Color decision helpers -------------
def co2_hue(value):
    if value < 1000:
        return H_GREEN
    if value < 1500:
        return H_YELLOW
    return H_RED

def worst_sensor_hue():
    if (
        var.led_request_co2 == "Red" or
        var.led_request_temp == "Red" or
        var.led_request_hum == "Red"
    ):
        return H_RED

    if (
        var.led_request_co2 == "Yellow" or
        var.led_request_temp == "Yellow" or
        var.led_request_hum == "Yellow"
    ):
        return H_YELLOW

    if (
        var.led_request_co2 == "Blue" or
        var.led_request_temp == "Blue" or
        var.led_request_hum == "Blue"
    ):
        return H_BLUE

    return H_GREEN

# ---- Breathing brightness helpers ------
def scale_breath_by_lux(v_breath, lux):
    # Pitch black: completely off
    if lux < LUX_OFF:
        return 0

    # Very low light: no animation, tiny fixed value
    if lux < LUX_LOW:
        return BREATH_MIN_VISIBLE

    lux_clamped = clamp(lux, LUX_LOW, LUX_MAX)
    t = (lux_clamped - LUX_LOW) / (LUX_MAX - LUX_LOW)
    scale = BREATH_SCALE_DARK + t * (BREATH_SCALE_BRIGHT - BREATH_SCALE_DARK)
    v_scaled = v_breath * scale

    # Avoid very low yellow becoming visually red
    if v_scaled < BREATH_MIN_VISIBLE:
        v_scaled = BREATH_MIN_VISIBLE

    return v_scaled

def next_breath_value(idx):
    v = BREATH_TABLE[idx]
    idx += 1
    if idx >= len(BREATH_TABLE):
        idx = 0

    return v, idx

def apply_breathing(np, h, idx):
    v_breath, idx = next_breath_value(idx)

    lux = var.sensor_data.lux_veml7700
    v_scaled = scale_breath_by_lux(v_breath, lux)
    v_scaled = smooth_breath(v_scaled)

    rgb = convert_hsv2rgb(h, SAT_FULL, v_scaled)
    fill(np, rgb)

    return idx

# ---- Animation effects -----------------
def apply_rainbow(np, phase):
    count = len(np)

    for i in range(count):
        h = phase + i * 360.0 / count
        np[i] = convert_hsv2rgb(h, SAT_FULL, RAINBOW_VALUE)

    np.write()

    phase += 10
    return phase

# ---- Main task--------------------------
async def led_task(period = 1.0):
    
    log = Logger("led", debug_enabled=False)
    
    pin = Pin(LED_PIN, Pin.OUT)
    np = neopixel.NeoPixel(pin, LED_COUNT)

    phase = 0
    breath_idx = 0
    
    #Run
    while True:
        # Startup / welcome screen
        if len(var.screen_names) == 0:
            fill(np, STARTUP_VALUE)

        # CO2 screens: breathing, color from CO2 level
        elif normal_screen_in(["CO2", "CO2 chart"]):
            h = co2_hue(var.sensor_data.co2_scd41)
            breath_idx = apply_breathing(np, h, breath_idx)

        # Sensors screen: breathing, color from worst sensor status
        elif normal_screen_active("Sensors"):
            h = worst_sensor_hue()
            breath_idx = apply_breathing(np, h, breath_idx)

        # Roll and Snake screens: static white-ish LEDs
        elif roll_or_snake_active():
            fill(np, STATIC_VALUE)

        # Default: rotating rainbow
        else:
            phase = apply_rainbow(np, phase)

        await asyncio.sleep(period)
        
        
