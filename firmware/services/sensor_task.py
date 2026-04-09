import uasyncio as asyncio
import time
import i2c
from machine import Pin, RTC
from logger import Logger
from drivers import veml7700 as veml7700_driver
from drivers import scd4x as scd4x_driver
from drivers import ds3231 as ds3231_driver

import math

# ---- Global variables ----
import shared_variables as var

log = Logger("i2c", debug_enabled=False)

def compensate_humidity(rh_raw: float, t_raw: float, t_cal: float) -> float:
    """
    rh_raw : raw relative humidity from sensor (%)
    t_raw  : raw (uncalibrated) temperature used by sensor (°C)
    t_cal  : calibrated / real temperature (°C)
    """

    # saturation vapor pressure (hPa)
    def esat(T):
        return 6.112 * math.exp((17.62 * T) / (243.12 + T))

    # actual vapor pressure stays constant
    e = (rh_raw / 100.0) * esat(t_raw)

    # recompute RH at corrected temperature
    rh_cal = 100.0 * e / esat(t_cal)

    # clamp to physical limits
    return max(0.0, min(100.0, rh_cal))

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

async def sensor_task(period = 1.0):
    #Init
    
    _SEN_SCL = const(38)
    _SEN_SDA = const(39)
    _SEN_I2C_FREQ = const(100000)
    i2c1_bus = i2c.I2C.Bus(host=1, scl=_SEN_SCL, sda=_SEN_SDA, freq=_SEN_I2C_FREQ, use_locks=False)
    log.info("Scan result:", i2c1_bus.scan())
    
    # Initialize the VEML7700 Lux sensor
    try:
        veml7700 = veml7700_driver.VEML7700(address=0x10, i2c=i2c1_bus, it=400, gain=1/8)
    except:
        log.error("VEML7700 cannot be initialized!")

    # Initialize the SCD4X CO2 sensor  
    try:
        scd4x = scd4x_driver.SCD4X(i2c1_bus)
        scd4x.set_ambient_pressure(969)
        scd4x.start_periodic_measurement()
    except:
        log.error("SCD41 cannot be initialized!")
    
    if var.hw_variant == "spi":
        # Initialize the DS3231 RTC
        try:
            ds3231 = ds3231_driver.DS3231(i2c1_bus)
            rtc_time = ds3231.datetime()
            var.system_data.time_rtc = rtc_time
            log.info("DS3231 RTC datetime at init:", rtc_time)
        except:
            log.error("DS3231 cannot be initialized!")

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

    i = 0

    #Run    
    while True:
        
        i+=1
        # Only scan devices in every 10th loop
        if i % 10 == 0:
            devices = i2c1_bus.scan()
            var.system_data.i2c_devices = devices
            
            # SCD41
            try:
                idx = devices.index(0x62)
                devices.pop(idx)
                var.system_data.i2c_status_scd41 = "SCD41 is online at 0x62"
            except:
                var.system_data.i2c_status_scd41 = "SCD41 is NOT found at 0x62"
                log.error("SCD41 is NOT found at 0x62")
            
            # VEML7700
            try:
                idx = devices.index(0x10)
                devices.pop(idx)
                var.system_data.i2c_status_veml7700 = "VEML7700 is online at 0x10"
            except:
                var.system_data.i2c_status_veml7700 = "VEML7700 is NOT found at 0x10"
                log.error("VEML7700 is NOT found at 0x10")
              
            var.system_data.i2c_status_unknown = devices

        try:
            lux = veml7700.read_lux()
            #log.debug("[VEML7700] Lux", lux)
            
            if lux is not None:
                lux_cal = 1.0 * lux - 0
                var.sensor_data.lux_veml7700 = lux_cal
            else:
                var.sensor_data.lux_veml7700 = 0
        except:
            log.error("VEML7700 communication error")
        
        try:
            co2 = scd4x.co2
            temp = scd4x.temperature
            rh = scd4x.relative_humidity
            #log.debug("[SCD41] CO2:", co2)
            #log.debug("[SCD41] temperature:", temp)
            #log.debug("[SCD41] humidity:", rh)
            var.sensor_data.co2_scd41 = co2 if co2 is not None else 0
            
            if temp is not None:
                temp_cal = 1 * temp - 0
                var.sensor_data.temp_scd41 = temp_cal
            else:
                temp_cal = 0.69
                var.sensor_data.temp_scd41 = temp_cal
            
            if rh is not None:
                rh_cal = compensate_humidity(rh, temp, temp_cal)
                var.sensor_data.humidity_scd41 = rh_cal
            else:
                var.sensor_data.humidity_scd41 = 0
            
        except:
            log.error("SCD41 communication error")


        if var.hw_variant == "spi" and i % 10 == 0:
            rtc_time = ds3231.datetime()
            rtc_temp = ds3231.temperature()
            #log.debug("DS3231 Time:", rtc_time)
            #log.debug("DS3231 Temperature:", rtc_temp)
            
            var.system_data.time_rtc = rtc_time
            var.sensor_data.temp_ds3231 = rtc_temp
            
            #log.debug("NTP time synchronized:", var.ntp_time_synchronized)
            if var.ntp_time_synchronized:
                #log.debug("RTC time:", var.system_data.time_rtc)
                #log.debug("NTP time:", time.localtime())
                if is_time_diff_over_threshold(time.localtime(), var.system_data.time_rtc, 60):
                    log.warning("RTC time needs to be updated from NTP time!")
                    log.warning("RTC time:", var.system_data.time_rtc)
                    log.warning("NTP time:", time.localtime())
                    ds3231.datetime(time.localtime())


        var.system_data.sensor_task_timestamp = time.time()
        
        await asyncio.sleep(period)

