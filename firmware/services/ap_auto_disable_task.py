import uasyncio as asyncio
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var
 
async def ap_auto_disable_task(period = 1.0):
    #Init
    log = Logger("ap_dis", debug_enabled=True)
    
    ap_start_ts = None
    AUTO_DISABLE_S = 120  # 2 minutes

    #Run
    while True:
        if var.ap_request:
            # First time AP request becomes active
            if ap_start_ts is None:
                ap_start_ts = time.time()
                log.debug("AP request detected, starting auto-disable timer")

            # Check timeout
            elapsed = time.time() - ap_start_ts
            if elapsed >= AUTO_DISABLE_S:
                log.info("AP auto-disabled after timeout")
                var.ap_request = False
                ap_start_ts = None
                
            var.ap_disable_timer = AUTO_DISABLE_S - elapsed

        else:
            # AP already disabled elsewhere → reset timer
            if ap_start_ts is not None:
                log.debug("AP request cleared externally, resetting timer")
            ap_start_ts = None

        await asyncio.sleep(period)


