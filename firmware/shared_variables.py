# shared_variables.py
import uasyncio as asyncio
import persistent_config

hw_variant = None # Can be "i80" or "spi"
debug = False
serial_number = 0
hostname = "CO2-Sensor-SNr"+str(serial_number)
temp_cal_A = 1
temp_cal_B = 0

class SimpleQueue:
    def __init__(self):
        self._items = []
        self._lock = asyncio.Lock()
        self._event = asyncio.Event()

    async def put(self, item):
        async with self._lock:
            self._items.append(item)
            self._event.set()

    def put_nowait(self, item):
        # Safe if everything runs on the same thread/core
        self._items.append(item)
        self._event.set()

    async def get(self):
        while True:
            await self._event.wait()

            async with self._lock:
                if self._items:
                    item = self._items.pop(0)

                    if not self._items:
                        self._event.clear()

                    return item
                else:
                    self._event.clear()

# Create a global queue instance
button_events = SimpleQueue()
audio_events = SimpleQueue()

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
        self.feedback_led = "green"
        self.buttons = [6,6,6]
        self.usb_connected = 0
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

free_space = 0
all_space = 0

display_view = 0

_http_lock = asyncio.Lock()

try:
    TZ_OFFSET = persistent_config.TZ_OFFSET
except:
    print("TZ offset cannot be read from persistent_config.py!")
    TZ_OFFSET = 0

ap_request = False
ap_enabled = False
ap_disable_timer = 69
wifi_connected = False
wifi_connecting = False
ntp_time_synchronized = False
rtc_time_synchronized = False
wifi_ready_evt = asyncio.Event()
first_connect = True
ssid_save_successful = False
wifi_ip = None
wifi_sleep = False
sleep_till_next_connection = 0

# screens are main screens, alt screens are a second page of screens
screens = []
screens_alt = []
screen_names = []
screen_names_alt = []
current_idx = 0
current_idx_alt = 0
selected_alt = 0

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
scd41_co2_max_display_history = 4*12 # 4 hours with 5min resolution

history_loaded = False

EVENT_AUDIO_SHORT = 1
EVENT_AUDIO_LONG = 2
EVENT_AUDIO_OFF = 3

led_request_co2 = "Green"
led_request_temp = "Green"
led_request_hum = "Green"