import uasyncio as asyncio
from logger import Logger
import time

# ---- Global variables ----
import shared_variables as var

async def asyncio_jitter_monitor(period_ms = 10):
    #Init
    log = Logger("scmon", debug_enabled=False)
    
    max_jitter = 0
    sum_jitter = 0
    samples = 0
    
    report_ms = 1000
    report_start = time.ticks_ms()

    while True:
        before = time.ticks_ms()

        await asyncio.sleep_ms(period_ms)

        after = time.ticks_ms()
        elapsed = time.ticks_diff(after, before)

        jitter = elapsed - period_ms

        if jitter > max_jitter:
            max_jitter = jitter

        samples += 1
        sum_jitter += jitter

        # report every 'report_ms'
        if time.ticks_diff(after, report_start) >= report_ms:
            avg_jitter = sum_jitter / samples

            log.info(f"Avg: {avg_jitter:.2f} ms | Max: {max_jitter} ms")

            # reset counters
            report_start = after
            samples = 0
            sum_jitter = 0
            max_jitter = 0