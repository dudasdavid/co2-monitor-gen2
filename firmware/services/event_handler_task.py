import uasyncio as asyncio
from logger import Logger
import time
import ui

# ---- Global variables ----
import shared_variables as var

EVENT_SHORT = 1
EVENT_LONG  = 2

async def event_handler_task():
    #Init
    log = Logger("evnt", debug_enabled=True)

    #Run
    while True:
        # wait for next event (this blocks until something arrives)
        btn_name, event_type = await var.button_events.get()

        if event_type == EVENT_SHORT:
            log.debug("SHORT press detected on:", btn_name)
            if btn_name == "down":
                ui.prev_screen(audio_feedback=False)
            elif btn_name == "up":
                ui.next_screen(audio_feedback=False)
            await var.audio_events.put(var.EVENT_AUDIO_SHORT)

        elif event_type == EVENT_LONG:
            log.debug("LONG press detected on:", btn_name)
            await var.audio_events.put(var.EVENT_AUDIO_LONG)

        else:
            log.debug("Unknown event:", btn_name, event_type)
