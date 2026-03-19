import uasyncio as asyncio
import time
import i2c
from logger import Logger
from drivers import veml7700 as veml7700_driver
from drivers import scd4x as scd4x_driver

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
            log.debug("[VEML7700] Lux", lux)
            
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
            log.debug("[SCD41] CO2:", co2)
            log.debug("[SCD41] temperature:", temp)
            log.debug("[SCD41] humidity:", rh)
            var.sensor_data.co2_scd41 = co2 if co2 is not None else 0
            
            if temp is not None:
                temp_cal = 0.98 * temp - 6.8
                var.sensor_data.temp_scd41 = temp_cal
            else:
                temp_cal = 0.69
                var.sensor_data.temp_scd41 = temp_cal
            
            if rh is not None:
                rh_cal = compensate_humidity(rh, temp, temp_cal)
                var.sensor_data.humidity_scd41 = rh_cal
            else:
                var.sensor_data.humidity_scd41 = 0
            
            # TODO: Should be moved to LED task
            if co2 == None:
                var.system_data.feedback_led = "off"
            elif co2 < 1000:
                var.system_data.feedback_led = "green"
            elif co2 < 1500:
                var.system_data.feedback_led = "yellow"
            else:
                var.system_data.feedback_led = "red"
        except:
            log.error("SCD41 communication error")
        
        var.system_data.sensor_task_timestamp = time.time()
        
        await asyncio.sleep(period)

