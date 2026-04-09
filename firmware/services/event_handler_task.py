import uasyncio as asyncio
from logger import Logger
import time
import ui
from lv_port import init

# ---- Global variables ----
import shared_variables as var

EVENT_SHORT = 1
EVENT_LONG  = 2

async def event_handler_task():
    #Init
    log = Logger("evnt", debug_enabled=True)
    lv = init()

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
            if btn_name == "power":
                await var.audio_events.put(var.EVENT_AUDIO_OFF)
            else:
                await var.audio_events.put(var.EVENT_AUDIO_LONG)
                if var.selected_alt == 0:
                    var.selected_alt = 1
                    ui.show_screen(var.current_idx_alt, lv.SCREEN_LOAD_ANIM.NONE)
                elif var.selected_alt == 1:
                    var.selected_alt = 0
                    ui.show_screen(var.current_idx, lv.SCREEN_LOAD_ANIM.NONE)
                else:
                    pass
                
        else:
            log.debug("Unknown event:", btn_name, event_type)
