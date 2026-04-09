from lv_port import init
import gc9a01
import lcd_bus
from machine import SPI, Pin, PWM
from micropython import const
import gc
import i2c  # NOQA
import task_handler  # NOQA
import cst816s

import uasyncio as asyncio
from services.idle_task import idle_task
from services.led_task import led_task
from services.backlight_task import backlight_task
from services.sensor_task import sensor_task
from services.io_expander_task import io_expander_task
from services.io_task import io_task
from services.imu_task import imu_task
from services.rtc_task import rtc_task
from services.adc_task import adc_task
from services.networking_task import networking_task
from services.history_task import history_task
from services.storage_task import storage_task
from services.audio_task import audio_task
from services.event_handler_task import event_handler_task
from services.ap_auto_disable_task import ap_auto_disable_task
from services.mqtt_task import mqtt_task

from logger import Logger

# ---- Global variables ----
import shared_variables as var

i2c_bus = None
# Default parameters
_WIDTH = const(240)
_HEIGHT = const(240)
# i80 display pins
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
_LCD_FREQ = const(6000000)
# SPI display pins
_LCD_SPI_FREQ = const(20000000)
_LCD_DC = const(18)
#_LCD_CS = const(2)
#_LCD_RST = const(21)
#_LCD_BACKLIGHT = const(42)
_SPI_HOST = const(1)
_SPI_SCK = const(3)
_SPI_MOSI = const(10)
_SPI_MISO = const(0)

_BUFFER_LINES = const(40)
_BUFFER_SIZE = const(240 * _BUFFER_LINES * 2)
#_BUFFER_SIZE = const(75000)

# touch device pins
_SCL = const(9)
_SDA = const(8)
_I2C_FREQ = const(100000)
_TP_RST = const(0)

def init_display_i80():
    # Initialize LVGL
    lv = init()

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

    # Set a big enough buffer to have smooth experiance (in expense of RAM)
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
    display.set_backlight(1) # It can be only 0 = OFF or 1 = ON, no dimming in display driver

    # Initialize I2C bus that has the touch controlelr (shared with IMU and IO expander)
    global i2c_bus
    i2c_bus = i2c.I2C.Bus(host=0, scl=_SCL, sda=_SDA, freq=_I2C_FREQ, use_locks=False)
    touch_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=cst816s.I2C_ADDR, reg_bits=cst816s.BITS)

    indev = cst816s.CST816S(touch_dev, reset_pin=_TP_RST)

    if not indev.is_calibrated:
        display.set_backlight(1)
        indev.calibrate()

    var.indev = indev

    # No idea what is exactly this
    th = task_handler.TaskHandler()

def init_display_spi():
    # Initialize LVGL
    lv = init()

    # Initialize the display bus
    spi_bus = SPI.Bus(
        host = _SPI_HOST,
        mosi = _SPI_MOSI,
        miso = _SPI_MISO,
        sck = _SPI_SCK
    )

    # Initialize the display bus
    display_bus = lcd_bus.SPIBus(
        spi_bus = spi_bus,
        dc = _LCD_DC,
        cs = _LCD_CS,
        freq=_LCD_SPI_FREQ 
    )

    # Set a big enough buffer to have smooth experience (in expense of RAM)
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
    display.set_backlight(1) # It can be only 0 = OFF or 1 = ON, no dimming in display driver

    # Initialize I2C bus that has the touch controlelr (shared with IMU and IO expander)
    i2c_bus = i2c.I2C.Bus(host=0, scl=_SCL, sda=_SDA, freq=_I2C_FREQ, use_locks=False)
    touch_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=cst816s.I2C_ADDR, reg_bits=cst816s.BITS)

    indev = cst816s.CST816S(touch_dev, reset_pin=_TP_RST)

    if not indev.is_calibrated:
        display.set_backlight(1)
        indev.calibrate()

    var.indev = indev

    # No idea what is exactly this
    th = task_handler.TaskHandler()

import ui

async def main():

    log = Logger("main", debug_enabled=False)
    
    # 0) start watchdog (optional)
    #wdt = machine.WDT(timeout=8000)
    
    # 1) initialize display
    if var.hw_variant == "i80":
        init_display_i80()
    elif var.hw_variant == "spi":
        init_display_spi()
    # Else is not needed because valid hw variants are already checked in main.py
    
    lv = init()
    global i2c_bus
    
    log.info("LVGL version:", lv.version_major(), lv.version_minor(), lv.version_patch())
    gc.collect()
    log.info("Free RAM at startup:", int(gc.mem_free() / 1024), "kB")
    
    ui.create_welcome_screen()
    
    # 2) spawn threads
    asyncio.create_task(sensor_task(0.3))
    asyncio.create_task(audio_task())
    await asyncio.sleep(6)
    asyncio.create_task(idle_task(5.0))
    asyncio.create_task(led_task(0.03))
    asyncio.create_task(backlight_task(0.1))
    asyncio.create_task(adc_task(1))
    asyncio.create_task(history_task(2))
    asyncio.create_task(storage_task(5))
    asyncio.create_task(event_handler_task())
    asyncio.create_task(networking_task(30, 60))
    asyncio.create_task(ap_auto_disable_task(1))
    asyncio.create_task(mqtt_task(10))
    
    if var.hw_variant == "i80":
        asyncio.create_task(io_expander_task(i2c_bus, 0.5))
        asyncio.create_task(imu_task(i2c_bus, 0.5))
        asyncio.create_task(rtc_task(i2c_bus, 2))
    elif var.hw_variant == "spi":
        asyncio.create_task(io_task(0.5))

    

    # 3) start UI  
    #top_layer = lv.layer_top()
    ui.create_sensor_table(alt = True)
    ui.create_co2_screen()
    ui.create_co2_chart_screen()
    ui.create_sensor_screen()
    ui.create_timezone_screen(alt = True)
    ui.create_ap_screen(alt = True)
    #ui.create_dummy_screen()
    ui.show_screen(0, lv.SCREEN_LOAD_ANIM.FADE_IN)   # start with screen 0
    #ui.create_status_bar(top_layer)

    log.info("Free RAM after UI:", int(gc.mem_free() / 1024), "kB")

    while True:     
              
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()