import uasyncio as asyncio
import time
from logger import Logger

# ---- Global variables ----
import shared_variables as var

async def history_task(period=1.0):
    # Init
    log = Logger("hist", debug_enabled=False)

    # 5 minutes window in ms
    WINDOW_MS = 5 * 60 * 1000

    # Accumulators for 5-minute average
    acc_sum = 0
    acc_count = 0
    window_start = time.ticks_ms()

    # Run
    while True:
        # --- sample current CO2 value ---
        value = var.sensor_data.co2_scd41

        # ignore None values, only accumulate real readings
        if value is not None:
            acc_sum += value
            acc_count += 1
            
            if var.scd41_co2_detected == 0 and value > var.scd41_co2_threshold:
                var.scd41_co2_detected = 1
            
            if var.scd41_co2_detected == 1 and value < var.scd41_co2_threshold - 50: # 50ppm hysteresis
                var.scd41_co2_detected = 0

        # --- update the live last element ---
        # last element must always represent current reading
        var.scd41_co2_history[-1] = value if value is not None else 0

        # check if 5 minutes passed
        now = time.ticks_ms()
        if time.ticks_diff(now, window_start) >= WINDOW_MS:
            if acc_count > 0:
                avg = acc_sum // acc_count   # integer average
            else:
                # no valid samples in this window → store 0
                avg = 0

            var.scd41_co2_history.pop() # remove the last item which is always the current value
            var.scd41_co2_history.append(avg)
            var.scd41_co2_history.append(avg) # append 2nd time so this will be overwritten by current value

            # trim old items if longer than allowed
            if len(var.scd41_co2_history) > var.CO2_HISTORY_MAX:
                overflow = len(var.scd41_co2_history) - var.CO2_HISTORY_MAX
                del var.scd41_co2_history[0:overflow]

            log.debug("Added CO2 history item:", avg,
                      "len:", len(var.scd41_co2_history))

            # reset window
            window_start = now
            acc_sum = 0
            acc_count = 0
            
            var.scd41_co2_peak_ppm = max(var.scd41_co2_history)
            
        # storage task recovered the last 24 hours log, check the peak
        if var.history_loaded:
            var.scd41_co2_peak_ppm = max(var.scd41_co2_history)
            log.info("History recovered, updating peak CO2")
            var.history_loaded = False # We don't need this flag anymore

        var.system_data.history_task_timestamp = time.time()

        await asyncio.sleep(period)