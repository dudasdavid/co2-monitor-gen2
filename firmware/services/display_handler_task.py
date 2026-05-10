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
        
        # On roll test screen disable screen rotation and disable WiFi
        if var.selected_alt and var.screen_names_alt[var.current_idx_alt] in ["Roll"]:
            display.set_rotation(lv.DISPLAY_ROTATION._0)
            var.wifi_disabled = True
        else:
            var.wifi_disabled = False
            if var.sensor_data.rpy[0] > 205 and var.sensor_data.rpy[0] < 320:
                display.set_rotation(lv.DISPLAY_ROTATION._270)
            elif var.sensor_data.rpy[0] > 40 and var.sensor_data.rpy[0] < 155:
                display.set_rotation(lv.DISPLAY_ROTATION._90)
            else:
                display.set_rotation(lv.DISPLAY_ROTATION._0)
        
        var.system_data.display_rotation_task_timestamp = time.time()
        
        await asyncio.sleep(period)
