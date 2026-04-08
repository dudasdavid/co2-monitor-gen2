import uasyncio as asyncio
from machine import Pin, RTC
import gc
from logger import Logger
import time
from drivers import pcf85063 as pcf85063_driver

# ---- Global variables ----
import shared_variables as var

log = Logger("rtc", debug_enabled=False)

def is_time_diff_over_threshold(ntp_time, rtc_time, threshold_seconds=60):
    """
    ntp_time and rtc_time are tuples like:
    (year, month, day, hour, minute, second, weekday, subsecond)

    Returns True if the absolute difference is > threshold_seconds (default 60s),
    otherwise False. If either is None or invalid, logs a warning and returns False.
    """
    if ntp_time is None or rtc_time is None:
        log.warning("NTP or RTC time is None, cannot compare.")
        return False

    try:
        # Unpack only the fields we actually need
        ny, nmo, nd, nh, nmin, ns, _, _ = ntp_time
        ry, rmo, rd, rh, rmin, rs, _, _ = rtc_time

        # Build time tuples compatible with time.mktime:
        # (year, month, mday, hour, minute, second, weekday, yearday)
        # weekday & yearday can be 0, they are usually ignored by mktime.
        ntp_struct = (ny, nmo, nd, nh, nmin, ns, 0, 0)
        rtc_struct = (ry, rmo, rd, rh, rmin, rs, 0, 0)

        ntp_seconds = time.mktime(ntp_struct)
        rtc_seconds = time.mktime(rtc_struct)

        diff = abs(ntp_seconds - rtc_seconds)
        return diff > threshold_seconds

    except Exception as e:
        log.warning("Failed to compare times:", ntp_time, rtc_time, "| Error:", e)
        return False

async def rtc_task(i2c_bus, period = 1.0):
    #Init
    pcf85063 = pcf85063_driver.PCF85063(i2c=i2c_bus, addr=0x51)
    
    #log.info("Scan result:", i2c_bus.scan())
    
    rtc_time = pcf85063.datetime()
    log.debug(rtc_time)
    
    var.system_data.time_rtc = rtc_time
    
    if not var.ntp_time_synchronized:
        rtc = RTC()
        
        # MicroPython RTC datetime format:
        # (year, month, day, weekday, hour, minute, second, subseconds)
        rtc.datetime((
            rtc_time[0],  # year
            rtc_time[1],  # month
            rtc_time[2],  # day
            rtc_time[6],  # weekday convert if needed
            rtc_time[3],  # hour
            rtc_time[4],  # minute
            rtc_time[5],  # second
            0
        ))
        var.rtc_time_synchronized = True
    
    #Test to intentionally cause a wrong RTC time
    #pcf85063.datetime((2022, 10, 9, 11, 11, 11, 0))

    #Run
    while True:
        
        rtc_time = pcf85063.datetime()
        log.debug(rtc_time)
        
        var.system_data.time_rtc = rtc_time
        
        log.debug("NTP time synchronized:", var.ntp_time_synchronized)
        if var.ntp_time_synchronized:
            log.debug("RTC time:", var.system_data.time_rtc)
            log.debug("NTP time:", time.localtime())
            if is_time_diff_over_threshold(time.localtime(), var.system_data.time_rtc, 60):
                log.warning("RTC time needs to be updated from NTP time!")
                log.warning("RTC time:", var.system_data.time_rtc)
                log.warning("NTP time:", time.localtime())
                pcf85063.datetime(time.localtime())
            
        
        await asyncio.sleep(period)
