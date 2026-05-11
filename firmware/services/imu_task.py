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
ATAN_LUT_SIZE = 128

atan_lut = [
    math.atan(i / ATAN_LUT_SIZE) * RAD_TO_DEG
    for i in range(ATAN_LUT_SIZE + 1)
]

ROLL_OFFSET = 0.0
ROLL_INVERT = False

G = 9.81
ACC_TRUST_MIN = 7.5
ACC_TRUST_MAX = 12.5

last_roll = 0.0
last_pitch = 0.0

def fast_atan_ratio(r):
    # r must be 0..1
    idx = int(r * ATAN_LUT_SIZE)
    if idx < 0:
        idx = 0
    elif idx > ATAN_LUT_SIZE:
        idx = ATAN_LUT_SIZE
    return atan_lut[idx]

def fast_atan2_deg(y, x):
    if x == 0:
        if y > 0:
            return 90.0
        if y < 0:
            return -90.0
        return 0.0

    ay = abs(y)
    ax = abs(x)

    if ax >= ay:
        a = fast_atan_ratio(ay / ax)
    else:
        a = 90.0 - fast_atan_ratio(ax / ay)

    if x >= 0:
        if y >= 0:
            return a
        else:
            return -a
    else:
        if y >= 0:
            return 180.0 - a
        else:
            return a - 180.0

def wrap_360(angle):
    angle = angle % 360
    if angle < 0:
        angle += 360
    return angle

def wrap_180(angle):
    return (angle + 180.0) % 360.0 - 180.0

def angle_lerp(a, b, t):
    d = wrap_180(b - a)
    return a + d * t

def calculate_roll_pitch(acc):
    global last_roll, last_pitch
    
    ax, ay, az = acc
    
    # Validate acceleration magnitude if there is any high force impact to reject
    acc_mag = math.sqrt(ax * ax + ay * ay + az * az)
    # Impact / acceleration rejection
    if acc_mag < ACC_TRUST_MIN or acc_mag > ACC_TRUST_MAX:
        log.warning("Acceleration input was rejected, using last calculated angles. Acceleration magnitude:", acc_mag)
        return last_roll, last_pitch
    
    # Pitch:
    # compare X gravity component against the remaining YZ gravity magnitude
    pitch_rad = -math.atan2(-ax, math.sqrt(ay * ay + az * az))

    # Roll:
    # compare Y gravity component against the remaining XZ gravity magnitude
    # this avoids rollover near vertical pitch
    roll_rad = math.atan2(ay, math.sqrt(ax * ax + az * az))

    roll_deg = math.degrees(roll_rad)
    pitch_deg = math.degrees(pitch_rad)

    if ROLL_INVERT:
        roll_deg = -roll_deg

    roll_deg = wrap_180(roll_deg - ROLL_OFFSET)
    
    last_roll = roll_deg
    last_pitch = pitch_deg

    return roll_deg, pitch_deg

def calculate_roll_pitch_simple_lut(acc):
    global last_roll, last_pitch
    
    ax, ay, az = acc

    # Validate acceleration magnitude if there is any high force impact to reject
    acc_mag = math.sqrt(ax * ax + ay * ay + az * az)
    # Impact / acceleration rejection
    if acc_mag < ACC_TRUST_MIN or acc_mag > ACC_TRUST_MAX:
        log.warning("Acceleration input was rejected, using last calculated angles. Acceleration magnitude:", acc_mag)
        return last_roll, last_pitch

    # pitch: X against the remaining gravity vector
    horiz_yz = math.sqrt(ay * ay + az * az)
    pitch_deg = -fast_atan2_deg(-ax, horiz_yz)

    # Continuous roll proxy:
    # use X when vertical, use Z when flat, smoothly via gravity vector magnitude
    roll_ref = math.sqrt(ax * ax + az * az)
    roll_deg = fast_atan2_deg(ay, roll_ref)

    if ROLL_INVERT:
        roll_deg = -roll_deg

    roll_deg = wrap_180(roll_deg - ROLL_OFFSET)
    
    last_roll = roll_deg
    last_pitch = pitch_deg
    
    return roll_deg, pitch_deg

async def imu_task(i2c_bus, period = 1.0):
    #Init
    
    imu_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=0x6b, reg_bits=8)
    imu = qmi8658c.QMI8658C(imu_dev, accel_range=qmi8658c.ACCEL_RANGE_4, gyro_range=qmi8658c.GYRO_RANGE_64)

    #Run
    while True:
        
        gyro = imu._get_gyrometer()
        await asyncio.sleep_ms(1)
        timestamp = imu.timestamp
        await asyncio.sleep_ms(1)
        temp = imu.temperature
        await asyncio.sleep_ms(1)
        acc = imu._get_accelerometer()
        
        #log.debug("Acc:", acc)
        #log.debug("Gyro:", gyro)
        #log.debug("Timestamp:", timestamp)
        #log.debug("Temp:", temp)
        
        var.sensor_data.temp_qmi8658c = temp
        var.sensor_data.acc_qmi8658c  = acc
        var.sensor_data.gyro_qmi8658c = gyro
        var.sensor_data.timestamp_qmi8658c  = timestamp
        
        #roll, pitch = calculate_roll_pitch(acc)
        roll, pitch = calculate_roll_pitch_simple_lut(acc)
        var.sensor_data.rpy = [roll, pitch, 0]
        
        var.system_data.imu_task_timestamp = time.time()
        
        await asyncio.sleep(period)

