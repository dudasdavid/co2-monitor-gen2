# shared_variables.py
import uasyncio as asyncio

hw_variant = None # Can be "i80" or "spi"

class SimpleQueue:
    def __init__(self):
        self._items = []
        self._lock = asyncio.Lock()

    async def put(self, item):
        async with self._lock:
            self._items.append(item)

    async def get(self):
        while True:
            async with self._lock:
                if self._items:
                    return self._items.pop(0)
            await asyncio.sleep_ms(10)

# Create a global queue instance
events = SimpleQueue()

async def post_event(ev):
    await events.put(ev)

class SensorData:
    def __init__(self):
        self.temp_scd41 = 6.9
        self.temp_qmi8658c = 16.9
        self.temp_ds3231 = 17.9
        self.humidity_scd41 = 26.9
        self.co2_scd41 = 666
        self.lux_veml7700 = 269.69
        self.acc_qmi8658c = (0,0,0)
        self.gyro_qmi8658c = (0,0,0)
        self.timestamp_qmi8658c = 69

class SystemData:
    def __init__(self):
        self.time_ntp = [1999, 1, 2, 11, 6, 11, 3, 78]
        self.time_rtc = [2001, 2, 3, 12, 9, 12, 4, 69]
        self.status_wifi = "Not Connected"
        self.status_ap = "Not Connected"
        self.status_sd = "Offline"
        self.total_space_flash = 690
        self.used_space_flash = 69
        self.total_space_sd = 6900
        self.used_space_sd = 69
        self.total_heap = 6900
        self.used_heap = 69
        self.bl_duty_percent = 34
        self.i2c_devices = []
        self.i2c_status_scd41  = "NA"
        self.i2c_status_aht21  = "NA"
        self.i2c_status_ens160  = "NA"
        self.i2c_status_bmp280  = "NA"
        self.i2c_status_veml7700  = "NA"
        self.i2c_status_ds3231  = "NA"
        self.i2c_status_pca9685  = "NA"
        self.i2c_status_drv2605  = "NA"
        self.i2c_status_unknown = [0x69]
        self.bat_volt = 3.8
        self.bat_percentage = 69
        self.charging = False
        self.feedback_led = "green"
        self.buttons = [0,1,2]
        self.usb_connected = 3
        self.adc_task_timestamp = 0
        self.backlight_task_timestamp = 0
        self.history_task_timestamp = 0
        self.sensor_task_timestamp = 0
        self.idle_task_timestamp = 0
        self.serial_task_timestamp = 0
        self.storage_task_timestamp = 0
        self.io_task_timestamp = 0
        self.io_expander_task_timestamp = 0
        self.imu_task_timestamp = 0

sensor_data = SensorData()
system_data = SystemData()

logger_debug = []
logger_info = []
logger_error = []
logger_warning = []

a = 0
b = 0
c = 0

scd41_co2_ppm = 0
scd41_temp_deg = 0
scd_41_humidity_percent = 0
aht21_temp_deg = 0
aht21_humidity_percent = 0
battery_voltage = 0
input_voltage = 0
analog_lux = 0
bmp280_pressure = 0
ens160_aqi = 0
ens160_tvoc = 0
ens160_tvoc_rating = 0
ens160_eco2 = 0
ens160_eco2_rating = 0
co2_history = []
max_history_samples = 60

free_space = 0
all_space = 0

display_view = 0

_http_lock = asyncio.Lock()

TZ_OFFSET = 1 * 3600

ap_request = False
ap_enabled = False
wifi_connected = False
wifi_connecting = False
ntp_time_synchronized = False
rtc_time_synchronized = False
wifi_ready_evt = asyncio.Event()
ssid_save_successful = False
wifi_ip = None
wifi_sleep = False
sleep_till_next_connection = 0

screens = []
screen_names = []
current_idx = 0

touch_start_x = 0
touch_start_y = 0
last_y = 0

indev = None

# Max number of samples you expect (24h at 5 min)
CO2_HISTORY_MAX = 12 * 24

scd41_co2_peak_ppm = 400
scd41_co2_threshold = 1800
scd41_co2_detected = 0
scd41_co2_history = [400] # Must contain 1 placeholder element
scd41_co2_max_display_history = 30

history_loaded = False
