from micropython import const
 
# registar overview - crtl & status reg
RTC_CTRL_1 = const(0x00)
RTC_CTRL_2 = const(0x01)
RTC_OFFSET = const(0x02)
RTC_RAM_by = const(0x03)

# registar overview - time & data reg
RTC_SECOND_ADDR = const(0x04)
RTC_MINUTE_ADDR = const(0x05)
RTC_HOUR_ADDR   = const(0x06)
RTC_DAY_ADDR    = const(0x07)
RTC_WDAY_ADDR   = const(0x08)
RTC_MONTH_ADDR  = const(0x09)
RTC_YEAR_ADDR   = const(0x0a) # years 0-99; calculate real year = 1970 + RCC reg year

def dectobcd(decimal):
    """Convert decimal to binary coded decimal (BCD) format"""
    return (decimal // 10) << 4 | (decimal % 10)

def bcdtodec(bcd):
    """Convert binary coded decimal to decimal"""
    return ((bcd >> 4) * 10) + (bcd & 0x0F)


class PCF85063:
    def __init__(self, i2c, addr=0x51):
        self.i2c = i2c
        self.addr = addr
        self._timebuf = bytearray(7) # Pre-allocate a buffer for the time data
        self._buf = bytearray(1)     # Pre-allocate a single bytearray for re-use

    def datetime(self, datetime=None):
        """Get or set datetime

        Always sets or returns in 24h format, converts to 24h if clock is set to 12h format
        datetime : tuple, (0-year, 1-month, 2-day, 3-hour, 4-minutes, 5-seconds, 6-weekday)"""
        if datetime is None:
            self.i2c.readfrom_mem_into(self.addr, RTC_SECOND_ADDR, self._timebuf)

            seconds = bcdtodec(self._timebuf[0] & 0x7f)
            minutes = bcdtodec(self._timebuf[1] & 0x7f)
            hour    = bcdtodec(self._timebuf[2] & 0x3f)
            day     = bcdtodec(self._timebuf[3] & 0x3f)
            weekday = bcdtodec(self._timebuf[4] & 0x07)
            month   = bcdtodec(self._timebuf[5] & 0x1f)
            year    = bcdtodec(self._timebuf[6]) + 1970

            return (year, month, day, hour, minutes, seconds, weekday, 0)

        # Set the clock
        self._timebuf[0] = dectobcd(datetime[5]) # Seconds
        self._timebuf[1] = dectobcd(datetime[4]) # Minutes
        self._timebuf[2] = dectobcd(datetime[3]) # Hour
        self._timebuf[3] = dectobcd(datetime[2]) # Day
        self._timebuf[4] = dectobcd(datetime[6]) # Day of week
        self._timebuf[5] = dectobcd(datetime[1]) # Month
        self._timebuf[6] = dectobcd(datetime[0] - 1970) # Year
        
        self.i2c.writeto_mem(self.addr, RTC_SECOND_ADDR, self._timebuf)
        return True


