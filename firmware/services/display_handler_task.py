import uasyncio as asyncio
import time
from logger import Logger
from lv_port import init

# ---- Global variables ----
import shared_variables as var
 
async def display_handler_task(display, period = 1.0):
    #Init
    lv = init()
    log = Logger("disp", debug_enabled=True)

    last_rotation = None
    last_backlight_override = None

    #Run
    while True:
        #log.debug("Task is running")
        
        # On roll test screen disable screen rotation
        if var.selected_alt and var.screen_names_alt[var.current_idx_alt] in ["Roll"]:
            target_rotation = lv.DISPLAY_ROTATION._0
            target_backlight_override = False
            
        # On snake screen set it to 90 degrees and disable screen rotation
        elif var.selected_game and var.screen_names_game[var.current_idx_game] in ["Snake"]:
            target_rotation = lv.DISPLAY_ROTATION._270
            target_backlight_override = True
            
        else:
            roll = var.sensor_data.rpy[0]
            
            if -90 < roll < -45:
                target_rotation = lv.DISPLAY_ROTATION._90
            elif 45 < roll < 90:
                target_rotation = lv.DISPLAY_ROTATION._270
            else:
                target_rotation = lv.DISPLAY_ROTATION._0

            target_backlight_override = False
        
        # -----------------------------
        # Apply only if changed
        # -----------------------------
        if target_rotation != last_rotation:
            display.set_rotation(target_rotation)
            last_rotation = target_rotation
            log.debug("Rotation changed:", target_rotation)

        if target_backlight_override != last_backlight_override:
            var.backlight_override = target_backlight_override
            last_backlight_override = target_backlight_override

        var.system_data.display_rotation_task_timestamp = time.time()
        
        await asyncio.sleep(period)
