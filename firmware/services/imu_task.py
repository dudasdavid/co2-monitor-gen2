import uasyncio as asyncio
from machine import Pin
from logger import Logger
import i2c
import qmi8658c
import time

# ---- Global variables ----
import shared_variables as var

log = Logger("imu", debug_enabled=False)

async def imu_task(i2c_bus, period = 1.0):
    #Init
    
    imu_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=0x6b, reg_bits=8)
    imu = qmi8658c.QMI8658C(imu_dev, accel_range=qmi8658c.ACCEL_RANGE_4, gyro_range=qmi8658c.GYRO_RANGE_64)

    #Run
    while True:
        
        acc = imu._get_accelerometer()
        gyro = imu._get_gyrometer()
        timestamp = imu.timestamp
        temp = imu.temperature
        
        #log.debug("Acc:", acc)
        #log.debug("Gyro:", gyro)
        #log.debug("Timestamp:", timestamp)
        #log.debug("Temp:", temp)
        
        var.sensor_data.temp_qmi8658c = temp
        var.sensor_data.acc_qmi8658c  = acc
        var.sensor_data.gyro_qmi8658c = gyro
        var.sensor_data.timestamp_qmi8658c  = timestamp
        
        var.system_data.imu_task_timestamp = time.time()
        
        await asyncio.sleep(period)

