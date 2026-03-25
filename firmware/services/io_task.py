import uasyncio as asyncio
from machine import Pin
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var

log = Logger("io", debug_enabled=False)   

DEBOUNCE_MS = const(40)
LONG_PRESS_MS = const(800)

EVENT_SHORT = const(1)
EVENT_LONG  = const(2)

BTN_UP   = const(14)
BTN_POW  = const(15)
BTN_DOWN = const(16)
BTN_USB  = const(17)

class ButtonHandler:
    def __init__(self, pin_num, name, index):
        self.name = name
        self.index = index
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)

        self.changed = False
        self.last_irq_ms = 0

        # Pin logic with PULL_UP:
        # 1 = released
        # 0 = pressed
        self.stable_state = self.pin.value()

        self.press_start_ms = None
        self.long_sent = False

        # Initialize global button state immediately
        var.system_data.buttons[self.index] = int(not self.stable_state)

        self.pin.irq(
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

    async def run(self):
        while True:
            if self.changed:
                self.changed = False

                # proper debounce in async context
                await asyncio.sleep_ms(DEBOUNCE_MS)

                current_state = self.pin.value()

                # bounced back -> ignore
                if current_state == self.stable_state:
                    await asyncio.sleep_ms(5)
                    continue

                self.stable_state = current_state
                now = time.ticks_ms()

                # update shared button array immediately
                # pressed -> 1, released -> 0
                var.system_data.buttons[self.index] = int(not current_state)

                if current_state == 0:
                    # pressed
                    self.press_start_ms = now
                    self.long_sent = False
                    asyncio.create_task(self._long_press_watch(self.press_start_ms))
                    log.debug("Pressed:", self.name)

                else:
                    # released
                    if self.press_start_ms is not None:
                        press_time = time.ticks_diff(now, self.press_start_ms)

                        if (not self.long_sent) and press_time < LONG_PRESS_MS:
                            await var.button_events.put((self.name, EVENT_SHORT))
                            log.debug("SHORT press:", self.name)

                    self.press_start_ms = None
                    self.long_sent = False
                    log.debug("Released:", self.name)

            await asyncio.sleep_ms(5)

    async def _long_press_watch(self, start_ms):
        await asyncio.sleep_ms(LONG_PRESS_MS)

        if (
            self.press_start_ms == start_ms and
            self.stable_state == 0 and
            not self.long_sent
        ):
            self.long_sent = True
            await var.button_events.put((self.name, EVENT_LONG))
            log.debug("LONG press:", self.name)

async def io_task(period = 1.0):
    # Init button handlers
    up_btn = ButtonHandler(BTN_UP, "up", 0)
    pow_btn = ButtonHandler(BTN_POW, "power", 1)
    down_btn = ButtonHandler(BTN_DOWN, "down", 2)

    # Separate pin for USB sense
    usb_pow_pin = Pin(BTN_USB, Pin.IN, Pin.PULL_UP)

    # Start button event tasks
    asyncio.create_task(up_btn.run())
    asyncio.create_task(pow_btn.run())
    asyncio.create_task(down_btn.run())

    #Run
    while True:
        
        # Only USB status is updated periodically in this main loop
        usb_conn = not usb_pow_pin.value()
        var.system_data.usb_connected = usb_conn
        
        var.system_data.io_task_timestamp = time.time()
        
        await asyncio.sleep(period)
