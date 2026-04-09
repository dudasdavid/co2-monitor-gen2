import uasyncio as asyncio
from machine import ADC, Pin
from logger import Logger
import utime

# ---- Global variables ----
import shared_variables as var

def corrected_voltage(v_measured):
    A = 1.0566
    B = 0.0277
    return A * v_measured + B

def lipo_voltage_to_percent(v):
    if v >= 4.1:
        return 100
    if v <= 3.10:
        return 0

    if v >= 4.0:
        return 90 + (v - 4.0) * 100
    elif v >= 3.8:
        return 70 + (v - 3.8) * 100
    elif v >= 3.6:
        return 50 + (v - 3.6) * 100
    elif v >= 3.4:
        return 30 + (v - 3.4) * 100
    elif v >= 3.2:
        return 10 + (v - 3.2) * 100
    else:
        return (v - 3.1) * 100

class BatteryFilter:
    def __init__(self,
                 ema_tau_s=10.0,     # time constant (seconds) -> larger = smoother
                 max_dv_per_s=0.03,  # volts/sec limit (prevents sudden jumps)
                 median_window=5):
        self.ema_tau_s = float(ema_tau_s)
        self.max_dv_per_s = float(max_dv_per_s)
        self.median_window = int(median_window)

        self._buf = []
        self._v_ema = None
        self._t_ms = None

    def update(self, v_raw):
        """Return filtered voltage."""
        now = utime.ticks_ms()

        # ---- dt ----
        if self._t_ms is None:
            dt = 0.5
        else:
            dt = utime.ticks_diff(now, self._t_ms) / 1000.0
            if dt <= 0:
                dt = 0.5
        self._t_ms = now

        # ---- median filter (spike killer) ----
        self._buf.append(float(v_raw))
        if len(self._buf) > self.median_window:
            self._buf.pop(0)

        # median without importing statistics (fast + small)
        s = sorted(self._buf)
        v_med = s[len(s)//2]

        # ---- rate limit voltage change ----
        if self._v_ema is None:
            v_limited = v_med
        else:
            max_step = self.max_dv_per_s * dt
            dv = v_med - self._v_ema
            if dv >  max_step: dv =  max_step
            if dv < -max_step: dv = -max_step
            v_limited = self._v_ema + dv

        # ---- EMA (low-pass) ----
        # alpha derived from tau and dt: alpha = dt/(tau+dt)
        alpha = dt / (self.ema_tau_s + dt)

        if self._v_ema is None:
            self._v_ema = v_limited
        else:
            self._v_ema = self._v_ema + alpha * (v_limited - self._v_ema)

        return self._v_ema

async def adc_task(period = 1.0):
    #Init
    log = Logger("adc", debug_enabled=False)
    

    adc1 = ADC(Pin(1)) # Battery voltage


    VREF = 3.3
    SCALE = VREF * 2 / 65535.0 # 2x due to 1:1 voltage divider

    bat_filt = BatteryFilter(
        ema_tau_s=12.0,     # 10–20s feels “solid” at 2Hz
        max_dv_per_s=0.02,  # battery cannot realistically change fast
        median_window=5
    )

    #Run
    while True:
        #log.debug("Task is running")

        raw_bat  = adc1.read_u16()

        
        # Convert to volts (approx; assumes ADC ref ~3.3V)
        v_bat = raw_bat * SCALE
        # Get calibrated voltage
        v_bat = corrected_voltage(v_bat)
        # Apply LPF
        v_bat_f = bat_filt.update(v_bat)
        var.system_data.bat_volt = v_bat_f
        # Calculate percentage
        var.system_data.bat_percentage = lipo_voltage_to_percent(v_bat_f)
        
        #log.debug("Battery voltage:", v_bat_f, "V, Percentage:", var.system_data.bat_percentage, "%")
    
        var.system_data.adc_task_timestamp = utime.time()
    
        await asyncio.sleep(period)
