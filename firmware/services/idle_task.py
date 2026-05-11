import uasyncio as asyncio
from machine import Pin
import gc
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var

async def idle_task(period = 1.0):
    #Init
    log = Logger("idle", debug_enabled=False)
    
    # Disable auto GC, we'll handle it by ourselves
    gc.disable()

    #Run
    while True:
        #log.debug("Task is running")
        # It's a bit counter-intuitive, but run gc.collect often, so we can avoid spikes in other asyncio tasks jitter
        gc.collect()
        free = gc.mem_free()
        used = gc.mem_alloc()
        total = free + used
        
        var.system_data.total_heap = total / 1024
        var.system_data.used_heap = used / 1024
        
        #log.debug("[MEM] total:", int(total / 1024), "kB, free:", int(free / 1024), "kB, used:", int(used / 1024), "kB")
        
        var.system_data.idle_task_timestamp = time.time()
        
        await asyncio.sleep(period)
