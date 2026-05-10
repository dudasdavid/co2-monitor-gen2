import uasyncio as asyncio
from machine import Pin
from logger import Logger
import i2c
import qmi8658c
import time
import math

# ---- Global variables ----
import shared_variables as var

log = Logger("imu", debug_enabled=False)

RAD_TO_DEG = 57.29577951308232

def wrap_360(angle):
    angle = angle % 360
    if angle < 0:
        angle += 360
    return angle

async def calculate_roll_pitch(acc):
    ax, ay, az = acc

    # 1) Calculate pitch first
    pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))
    await asyncio.sleep_ms(20)

    cp = math.cos(pitch)
    sp = math.sin(pitch)
    await asyncio.sleep_ms(20)

    # 2) Rotate acceleration vector back by pitch
    # This removes pitch influence before calculating roll
    ay2 = ay
    az2 = ax * sp + az * cp

    # 3) Calculate roll from pitch-compensated Y/Z
    roll = - math.atan2(ay2, az2)
    await asyncio.sleep_ms(20)

    roll_deg = wrap_360(roll * RAD_TO_DEG)
    pitch_deg = -(pitch * RAD_TO_DEG)

    return roll_deg, pitch_deg

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
        
        roll, pitch = await calculate_roll_pitch(acc)
        var.sensor_data.rpy = [roll, pitch, 0]
        
        var.system_data.imu_task_timestamp = time.time()
        
        await asyncio.sleep(period)

