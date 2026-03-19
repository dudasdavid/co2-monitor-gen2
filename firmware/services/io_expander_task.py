import uasyncio as asyncio
from machine import Pin
from logger import Logger
import i2c
import tca6408
import io_expander_framework
import time

# ---- Global variables ----
import shared_variables as var

log = Logger("ioex", debug_enabled=True)

def irq_handler(pin):
    log.debug("Interrupt from pin:", pin)
    
    # IO expander returns 0 if input is true and 1 if false
    up = int(not up_pin.value())
    down = int(not down_pin.value())
    power = int(not pow_pin.value())
    usb_conn = not usb_pow_pin.value()
    
    var.system_data.buttons = [up, power, down]
    var.system_data.usb_connected = usb_conn
    

async def io_expander_task(i2c_bus, period = 1.0):
    #Init    
    # GPIO45 as input (no pull!)
    pin45 = Pin(45, Pin.IN, Pin.PULL_UP)

    # Attach interrupt
    pin45.irq(
        trigger=Pin.IRQ_RISING,
        handler=irq_handler
    )

    io_expander_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=0x20, reg_bits=8)
    #tca6408.Pin.set_device(io_expander_dev)
    io_expander_framework.Pin.set_device(io_expander_dev)

    up_pin = tca6408.Pin(tca6408.EXIO4, mode=tca6408.Pin.IN)      # P3
    pow_pin = tca6408.Pin(tca6408.EXIO5, mode=tca6408.Pin.IN)     # P4
    down_pin = tca6408.Pin(tca6408.EXIO6, mode=tca6408.Pin.IN)    # P5
    usb_pow_pin = tca6408.Pin(tca6408.EXIO7, mode=tca6408.Pin.IN) # P6

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
        
        var.system_data.io_expander_task_timestamp = time.time()
        
        await asyncio.sleep(period)
