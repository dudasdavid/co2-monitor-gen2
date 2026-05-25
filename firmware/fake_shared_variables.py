
hw_variant = "i80"

class SensorData:
    def __init__(self):
        self.temp_scd41 = 16.9
        self.temp_qmi8658c = 18.2
        self.temp_ds3231 = 17.7
        self.humidity_scd41 = 69
        self.co2_scd41 = 420
        self.lux_veml7700 = 270.25
        self.acc_qmi8658c = (0.5,0.22,9.81)
        self.gyro_qmi8658c = (1.3,1.5,0.9)
        self.rpy = (10,60,0)

class SystemData:
    def __init__(self):
        self.time_ntp = [1999, 1, 2, 11, 6, 11, 3, 78]
        self.time_rtc = [2001, 2, 3, 12, 9, 12, 4, 69]
        self.status_wifi = "192.168.1.69"
        self.status_ap = "Not Connected"
        self.mqtt_server_connection = "Remote"
        self.total_space_flash = 16000
        self.used_space_flash = 1200
        self.total_heap = 8900
        self.used_heap = 200
        self.bat_volt = 3.2
        self.bat_percentage = 5
        self.buttons = [0,0,1]
        self.usb_connected = 1

sensor_data = SensorData()
system_data = SystemData()

TZ_OFFSET = 2*60*60 # In seconds, e.g. for UTC+2: 2*60*60

wifi_disabled = False
ap_request = False
ap_enabled = False
ap_disable_timer = 69
wifi_connected = True
wifi_connecting = False
ntp_time_synchronized = False
rtc_time_synchronized = False
first_connect = True
ssid_save_successful = False
wifi_ip = "192.168.1.69"
wifi_sleep = False
sleep_till_next_connection = 0

# screens are main screens, alt screens are a second page of screens
screens = []
screens_alt = []
screens_game = []
screen_names = []
screen_names_alt = []
screen_names_game = []
current_idx = 0
current_idx_alt = 0
current_idx_game = 0
# flag to show if alternative or game screen is selected
selected_alt = 0
selected_game = 0

# Max number of samples you expect (24h at 5 min)
CO2_HISTORY_MAX = 12 * 24

scd41_co2_peak_ppm = 400
scd41_co2_threshold = 1800
scd41_co2_detected = 0

scd41_co2_history = [
    500, 595, 700, 795, 880, 920, 950, 950,
    922, 890, 838, 800, 760, 722, 688, 660,
    638, 622, 610, 603, 600, 606, 620, 642,
    672, 710, 757, 813, 878, 952, 1035, 1127,
    1228, 1338, 1457, 1585, 1720, 1760, 1800, 1798,
    1795, 1791, 1786, 1780, 1773, 1765, 1756, 1746
]

scd41_co2_max_display_history = 4*12 # 4 hours with 5min resolution

history_loaded = True

