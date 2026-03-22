import uasyncio as asyncio
from machine import Pin
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var

log = Logger("io", debug_enabled=True)

def irq_handler(pin):
    log.debug("Interrupt from pin:", pin)
    
    # IO expander returns 0 if input is true and 1 if false
    up = int(not up_pin.value())
    down = int(not down_pin.value())
    power = int(not pow_pin.value())
    usb_conn = not usb_pow_pin.value()
    
    var.system_data.buttons = [up, power, down]
    var.system_data.usb_connected = usb_conn
    

async def io_task(period = 1.0):
    #Init    
    # GPIO45 as input (no pull!)
    #pin45 = Pin(45, Pin.IN, Pin.PULL_UP)
    
    up_pin = Pin(14, Pin.IN, Pin.PULL_UP)
    pow_pin = Pin(15, Pin.IN, Pin.PULL_UP)
    down_pin = Pin(16, Pin.IN, Pin.PULL_UP)
    usb_pow_pin = Pin(17, Pin.IN, Pin.PULL_UP)

    # Attach interrupt
    #pin45.irq(
    #    trigger=Pin.IRQ_RISING,
    #    handler=irq_handler
    #)

    #Run
    while True:
        
        # IO expander returns 0 if input is true and 1 if false
        up = int(not up_pin.value())
        down = int(not down_pin.value())
        power = int(not pow_pin.value())
        usb_conn = not usb_pow_pin.value()
        
        var.system_data.buttons = [up, power, down]
        var.system_data.usb_connected = usb_conn
        
        
        log.debug("UP:", up, "DOWN:", down, "POW:", power)
        
        var.system_data.io_task_timestamp = time.time()
        
        await asyncio.sleep(period)
