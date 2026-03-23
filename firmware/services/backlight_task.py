import uasyncio as asyncio
from logger import Logger
import time
from machine import Pin, PWM

# ---- Global variables ----
import shared_variables as var
_LCD_BACKLIGHT = const(42)

async def backlight_task(period = 1.0):
    #Init
    log = Logger("bclt", debug_enabled=False)
    
    pwm = PWM(Pin(_LCD_BACKLIGHT))
    pwm.freq(20000)
    pwm.duty_u16(10000)
    
    lux_min=2.0       # below this treat as "dark"
    lux_max=120.0     # above this -> max backlight
    duty_min=8        # min duty on your 0..100 scale (to avoid pitch black)
    duty_max=1000     # max duty
    gamma=0.6         # >1.0 compresses the low end (fixes "too bright at 10–15%")
    alpha=0.3         # smoothing factor (0..1), 0=no change, 1=no smoothing
    _level = 1.0      # internal smoothed brightness level [0..1]
    _duty = 1000.0    # default level is 1 (max) and duty is 1000 (max) to show welcome screen with high brigthness
    max_step = 30 

    def _lux_to_level(lux):
        """Map lux → linear brightness level [0..1] (before gamma)."""
        if lux <= lux_min:
            return 0.0
        if lux >= lux_max:
            return 1.0

        # Normalize
        return (lux - lux_min) / (lux_max - lux_min)

    def _level_to_duty(level):
        """Map brightness level [0..1] → integer duty [duty_min..duty_max]."""
        # Clamp
        if level < 0.0:
            level = 0.0
        elif level > 1.0:
            level = 1.0

        # Apply gamma so small levels don't jump to "too bright"
        # hardware_effective = level ** gamma
        level_gamma = level ** gamma

        duty_range = duty_max - duty_min
        duty = duty_min + duty_range * level_gamma
        duty = int(duty + 0.5)
        
        if duty < 0:
            duty = 0
        elif duty > 1000:
            duty = 1000
            
        return duty
        
    def _slew_limit(current, target, max_delta):
        """Move current toward target by at most max_delta (both can be float/int)."""
        diff = target - current
        if diff > max_delta:
            return current + max_delta
        if diff < -max_delta:
            return current - max_delta
        return target

    #Run
    while True:
        log.debug("Measured lux:", var.sensor_data.lux_veml7700)
        
        raw_level = _lux_to_level(var.sensor_data.lux_veml7700)
        # Exponential smoothing to avoid flicker (optional)
        _level = (1.0 - alpha) * _level + alpha * raw_level
        _target_duty = _level_to_duty(_level)
        _duty = _slew_limit(_duty, _target_duty, max_step)
            
        log.debug("Calculated duty [0-1000]:", _duty)
        var.system_data.bl_duty_percent = int(_duty)
        
        pwm.duty_u16(int(_duty*65.535)) # calculate the 0...1000 range to 0...65535 (uint_16)
        
        var.system_data.backlight_task_timestamp = time.time()
        
        await asyncio.sleep(period)
