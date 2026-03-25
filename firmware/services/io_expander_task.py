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

DEBOUNCE_MS = const(40)
LONG_PRESS_MS = const(800)

EVENT_SHORT = const(1)
EVENT_LONG  = const(2)

PIN_IOEXP   = const(45)

IDX_UP   = const(0)
IDX_POW  = const(1)
IDX_DOWN = const(2)

class IOExpanderHandler:
    def __init__(self, pin_num):
        self.name = "ioexp_irq"
        self.irq_pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)

        self.changed = False
        self.last_irq_ms = 0

        self.up_pin = tca6408.Pin(tca6408.EXIO4, mode=tca6408.Pin.IN)      # P3
        self.pow_pin = tca6408.Pin(tca6408.EXIO5, mode=tca6408.Pin.IN)     # P4
        self.down_pin = tca6408.Pin(tca6408.EXIO6, mode=tca6408.Pin.IN)    # P5
        self.usb_pow_pin = tca6408.Pin(tca6408.EXIO7, mode=tca6408.Pin.IN) # P6

        # Stable logical button states:
        # 0 = released
        # 1 = pressed
        self.button_states = {
            "up": self._read_button_logical(self.up_pin),
            "power": self._read_button_logical(self.pow_pin),
            "down": self._read_button_logical(self.down_pin),
        }

        # Per-button press tracking
        self.press_start_ms = {
            "up": None,
            "power": None,
            "down": None,
        }

        self.long_sent = {
            "up": False,
            "power": False,
            "down": False,
        }

        # Init shared vars immediately
        var.system_data.buttons = [
            self.button_states["up"],
            self.button_states["power"],
            self.button_states["down"],
        ]
        var.system_data.usb_connected = self._read_usb_logical()

        # Attach IRQ on the shared expander interrupt pin
        self.irq_pin.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
            handler=self._irq_handler
        )


    def _irq_handler(self, pin):
        now = time.ticks_ms()

        # tiny debounce at IRQ side
        if time.ticks_diff(now, self.last_irq_ms) < 5:
            return

        self.last_irq_ms = now
        self.changed = True

    def _read_button_logical(self, pin_obj):
        # IO expander returns 0 when pressed, 1 when released
        # Convert to logical: pressed=1, released=0
        return int(not pin_obj.value())

    def _read_usb_logical(self):
        return not self.usb_pow_pin.value()

    def _refresh_shared_states(self):
        var.system_data.buttons = [
            self.button_states["up"],
            self.button_states["power"],
            self.button_states["down"],
        ]
        var.system_data.usb_connected = self._read_usb_logical()

    async def _handle_button_change(self, btn_name, new_state, now_ms):
        old_state = self.button_states[btn_name]

        if new_state == old_state:
            return

        self.button_states[btn_name] = new_state
        self._refresh_shared_states()

        if new_state == 1:
            # pressed
            self.press_start_ms[btn_name] = now_ms
            self.long_sent[btn_name] = False
            asyncio.create_task(self._long_press_watch(btn_name, now_ms))
            log.debug("Pressed:", btn_name)

        else:
            # released
            start_ms = self.press_start_ms[btn_name]
            if start_ms is not None:
                press_time = time.ticks_diff(now_ms, start_ms)

                if (not self.long_sent[btn_name]) and press_time < LONG_PRESS_MS:
                    await var.button_events.put((btn_name, EVENT_SHORT))
                    log.debug("SHORT press:", btn_name)

            self.press_start_ms[btn_name] = None
            self.long_sent[btn_name] = False
            log.debug("Released:", btn_name)

    async def run(self):
        while True:
            if self.changed:
                self.changed = False

                # Proper debounce in async context
                await asyncio.sleep_ms(DEBOUNCE_MS)

                now = time.ticks_ms()

                # Read all current logical states from expander
                up_now = self._read_button_logical(self.up_pin)
                pow_now = self._read_button_logical(self.pow_pin)
                down_now = self._read_button_logical(self.down_pin)
                usb_now = self._read_usb_logical()

                # Process button changes individually
                await self._handle_button_change("up", up_now, now)
                await self._handle_button_change("power", pow_now, now)
                await self._handle_button_change("down", down_now, now)

                # USB is just state, no short/long event
                if usb_now != var.system_data.usb_connected:
                    var.system_data.usb_connected = usb_now
                    log.debug("USB connected:", usb_now)

            await asyncio.sleep_ms(5)

    async def _long_press_watch(self, btn_name, start_ms):
        await asyncio.sleep_ms(LONG_PRESS_MS)

        # Still same press cycle and still pressed?
        if (
            self.press_start_ms[btn_name] == start_ms and
            self.button_states[btn_name] == 1 and
            not self.long_sent[btn_name]
        ):
            self.long_sent[btn_name] = True
            await var.button_events.put((btn_name, EVENT_LONG))
            log.debug("LONG press:", btn_name)

async def io_expander_task(i2c_bus, period = 1.0):
    #Init       
    io_expander_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=0x20, reg_bits=8)
    io_expander_framework.Pin.set_device(io_expander_dev)
    
    # GPIO45 as IO expander input
    ioexp = IOExpanderHandler(PIN_IOEXP)
    asyncio.create_task(ioexp.run())

    #Run
    while True:
        
        var.system_data.io_expander_task_timestamp = time.time()
        await asyncio.sleep(period)
