# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import sys
LOG_FILE = "/startup_error.log"

def log_exception(exc):
    try:
        with open(LOG_FILE, "a") as f:
            f.write("\n\n=== BOOT ERROR ===\n")
            sys.print_exception(exc, f)
            f.write("\n")
    except:
        pass

try:
    from machine import Pin
    import neopixel

    STARTUP_VALUE = (30, 30, 100)
    LED_PIN   = const(43)
    LED_COUNT = const(18)

    pin = Pin(LED_PIN, Pin.OUT)
    np = neopixel.NeoPixel(pin, LED_COUNT)

    def fill(np, rgb):
        for i in range(len(np)):
            np[i] = rgb
        np.write()
        
    fill(np, STARTUP_VALUE)
        
except Exception as e:
    log_exception(e)
    