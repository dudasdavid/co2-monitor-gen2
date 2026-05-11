import uasyncio as asyncio
import time
from logger import Logger
from lv_port import init

# ---- Global variables ----
import shared_variables as var
 
async def display_handler_task(display, period = 1.0):
    #Init
    lv = init()
    log = Logger("disp", debug_enabled=False)

    #Run
    while True:
        #log.debug("Task is running")
        
        # On roll test screen disable screen rotation
        if var.selected_alt and var.screen_names_alt[var.current_idx_alt] in ["Roll"]:
            display.set_rotation(lv.DISPLAY_ROTATION._0)
        else:
            if var.sensor_data.rpy[0] > -90 and var.sensor_data.rpy[0] < -45:
                display.set_rotation(lv.DISPLAY_ROTATION._90)
            elif var.sensor_data.rpy[0] > 45 and var.sensor_data.rpy[0] < 90:
                display.set_rotation(lv.DISPLAY_ROTATION._270)
            else:
                display.set_rotation(lv.DISPLAY_ROTATION._0)
        
        var.system_data.display_rotation_task_timestamp = time.time()
        
        await asyncio.sleep(period)
