import lvgl as lv
import gc9a01
import lcd_bus
from machine import SPI, Pin, PWM
from micropython import const

_WIDTH = const(240)
_HEIGHT = const(240)

_LCD_CS = const(2)
_LCD_WRB = const(3)
_LCD_D0 = const(10)
_LCD_D1 = const(11)
_LCD_D2 = const(12)
_LCD_D3 = const(13)
_LCD_D4 = const(14)
_LCD_D5 = const(15)
_LCD_D6 = const(16)
_LCD_D7 = const(17)
_LCD_RS = const(18)
_LCD_RST = const(21)
_LCD_BACKLIGHT = const(42)
_LCD_FREQ = const(40000000)

_SCL = const(9)
_SDA = const(8)
_I2C_FREQ = const(100000)
_TP_RST = const(0)

# Initialize LVGL
lv.init()

# Initialize the display bus
display_bus = lcd_bus.I80Bus(
    dc = _LCD_RS,
    wr = _LCD_WRB,
    freq=_LCD_FREQ,
    data0=_LCD_D0,
    data1=_LCD_D1,
    data2=_LCD_D2,
    data3=_LCD_D3,
    data4=_LCD_D4,
    data5=_LCD_D5,
    data6=_LCD_D6,
    data7=_LCD_D7
)

_BUFFER_SIZE = const(57600)
fb1 = display_bus.allocate_framebuffer(_BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
fb2 = display_bus.allocate_framebuffer(_BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)

# Initialize the GC9A01 display driver
display = gc9a01.GC9A01(
    data_bus = display_bus,
    frame_buffer1=fb1,
    frame_buffer2=fb2,
    display_width = _WIDTH,
    display_height = _HEIGHT,
    reset_pin = _LCD_RST,
    reset_state = gc9a01.STATE_LOW,
    power_on_state = gc9a01.STATE_HIGH,
    backlight_pin=_LCD_BACKLIGHT,
    offset_x=0,
    offset_y=0,
    color_space=lv.COLOR_FORMAT.RGB565,
    rgb565_byte_swap=True
)


# Initialize display
display.set_power(True)
display.init()
display.set_backlight(1)

import i2c  # NOQA
import task_handler  # NOQA
import cst816s

i2c_bus = i2c.I2C.Bus(host=0, scl=_SCL, sda=_SDA, freq=_I2C_FREQ, use_locks=False)
touch_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=cst816s.I2C_ADDR, reg_bits=cst816s.BITS)

indev = cst816s.CST816S(touch_dev, reset_pin=_TP_RST)

if not indev.is_calibrated:
    display.set_backlight(1)
    indev.calibrate()

#display.set_backlight(10)
pwm = PWM(Pin(_LCD_BACKLIGHT))
pwm.freq(20000)
pwm.duty_u16(5000)

th = task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0x000000), 0)

slider = lv.slider(scrn)
slider.set_size(180, 50)
slider.center()

label = lv.label(scrn)
label.set_text('HELLO WORLD!')
label.align(lv.ALIGN.CENTER, 0, -50)

import qmi8658c
imu_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=0x6b, reg_bits=8)
imu = qmi8658c.QMI8658C(imu_dev, accel_range=qmi8658c.ACCEL_RANGE_4, gyro_range=qmi8658c.GYRO_RANGE_64)
import time



def irq_handler(pin):
    print("Interrupt from pin:", pin)

# GPIO45 as input (no pull!)
pin45 = Pin(45, Pin.IN, Pin.PULL_UP)

# Attach interrupt
pin45.irq(
    trigger=Pin.IRQ_RISING,
    handler=irq_handler
)


import tca6408
import io_expander_framework
io_expander_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=0x20, reg_bits=8)
#tca6408.Pin.set_device(io_expander_dev)
io_expander_framework.Pin.set_device(io_expander_dev)

up_pin = tca6408.Pin(tca6408.EXIO4, mode=tca6408.Pin.IN)
pow_pin = tca6408.Pin(tca6408.EXIO5, mode=tca6408.Pin.IN)
down_pin = tca6408.Pin(tca6408.EXIO6, mode=tca6408.Pin.IN)

_SEN_SCL = const(38)
_SEN_SDA = const(39)
_SEN_I2C_FREQ = const(100000)
i2c1_bus = i2c.I2C.Bus(host=1, scl=_SEN_SCL, sda=_SEN_SDA, freq=_SEN_I2C_FREQ, use_locks=False)
print(i2c1_bus.scan())

try:
    from drivers import scd4x as scd4x_driver
    scd4x = scd4x_driver.SCD4X(i2c1_bus)
    scd4x.start_periodic_measurement()
except:
    print("SCD41 cannot be initialized!")

while True:
    print("Acc:", imu._get_accelerometer())
    print("Gyro:", imu._get_gyrometer())
    print("Timestamp:", imu.timestamp)
    print("Temp:", imu.temperature)
    print("UP:", up_pin.value(), "DOWN:", down_pin.value(), "POW:", pow_pin.value())
    
    try:
        co2 = scd4x.co2
        temp = scd4x.temperature
        rh = scd4x.relative_humidity
        print("[SCD41] CO2:", co2)
        print("[SCD41] temperature:", temp)
        print("[SCD41] humidity:", rh)
    except:
        print("SCD41 is not connected!")
    
    time.sleep(1)

