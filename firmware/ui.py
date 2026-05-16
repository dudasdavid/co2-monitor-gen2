from lv_port import init
from math import ceil, sin
import time
import random
import math

# ---- Global variables ----
import shared_variables as var

SCREEN_H = 240
SCREEN_W = 240
STATUS_BAR_H = 24
PAGE_W_PADDING = 0

# ---- Swipe handling ----
SWIPE_THRESHOLD = 40   # pixels
LOCK_THRESHOLD  = 12  # when horizontal movement is clearly starting

def localtime_with_offset(offset_sec=var.TZ_OFFSET):
    # get current UTC epoch
    utc_epoch = time.time()
        
    # apply offset
    local_epoch = utc_epoch + offset_sec
    
    # convert back to tuple
    return time.localtime(local_epoch)

# ---- LVGL helper functions ----
def show_screen(idx, lv_animation):
    """Load screen by index (wrap around)."""
    lv = init()
    if not var.screens:
        return
    
    # If alt screens carousel is selected (settings screens)
    if var.selected_alt == 1:
        var.current_idx_alt = idx % len(var.screens_alt)
        screen = var.screens_alt[var.current_idx_alt]
    # If game screens carousel is selected
    elif var.selected_game == 1:
        var.current_idx_game = idx % len(var.screens_game)
        screen = var.screens_game[var.current_idx_game]
    # Normal - usually sensor - screens carousel is selected
    else:
        var.current_idx = idx % len(var.screens)
        screen = var.screens[var.current_idx]
        
    #lv.screen_load(var.screens[var.current_idx])
    lv.screen_load_anim(
        screen,
        lv_animation, # animation type
        30,           # duration in ms
        0,            # delay in ms
        False         # auto delete old screen
    )

def next_screen(audio_feedback=True):
    lv = init()
    if var.selected_alt == 1:
        idx = var.current_idx_alt + 1
    elif var.selected_game == 1:
        idx = var.current_idx_game + 1
    else:
        idx = var.current_idx + 1
        
    show_screen(idx, lv.SCREEN_LOAD_ANIM.NONE) # OUT_LEFT
    
    if audio_feedback:
        var.audio_events.put_nowait(var.EVENT_AUDIO_SHORT)

def prev_screen(audio_feedback=True):
    lv = init()
    if var.selected_alt == 1:
        idx = var.current_idx_alt - 1
    elif var.selected_game == 1:
        idx = var.current_idx_game - 1
    else:
        idx = var.current_idx - 1
    
    show_screen(idx, lv.SCREEN_LOAD_ANIM.NONE) # OUT_RIGHT
    
    if audio_feedback:
        var.audio_events.put_nowait(var.EVENT_AUDIO_SHORT)
        
def swipe_event_cb(e):
    lv = init()

    if e.get_code() == lv.EVENT.GESTURE:
        pass
    elif e.get_code() == lv.EVENT.LONG_PRESSED:
        #print("Long press received")
        return
    elif e.get_code() == lv.EVENT.DOUBLE_CLICKED:
        #print("Double click received")
        return
    elif e.get_code() == lv.EVENT.RELEASED:
        #print("Released received")
        return
    else:
        return

    indev = var.indev
    if not indev:
        return

    d = indev.get_gesture_dir()
    
    if d == lv.DIR.LEFT:
        next_screen()
    elif d == lv.DIR.RIGHT:
        prev_screen()

def create_battery_widget(parent, x, y, font=None):
    lv = init()

    root = lv.obj(parent)
    root.set_size(50, 50)
    root.align(lv.ALIGN.CENTER, x, y)
    root.set_style_bg_opa(lv.OPA.TRANSP, 0)
    root.set_style_border_width(0, 0)
    root.set_style_pad_all(0, 0)
    root.remove_flag(lv.obj.FLAG.SCROLLABLE)

    # Battery icon
    icon = lv.label(root)
    icon.set_text(lv.SYMBOL.BATTERY_FULL)
    icon.set_style_text_color(lv.color_hex(0x666666), 0)
    icon.set_style_text_letter_space(0, 0)
    icon.set_style_text_line_space(0, 0)

    if font:
        icon.set_style_text_font(font, 0)

    icon.align(lv.ALIGN.CENTER, 0, 0)

    # Charging icon overlay
    charge_shadow = lv.label(root)
    charge_shadow.set_text(lv.SYMBOL.CHARGE)
    charge_shadow.set_style_text_color(lv.color_hex(0x000000), 0)
    charge_shadow.align_to(icon, lv.ALIGN.CENTER, -1, 0)
    charge_shadow.add_flag(lv.obj.FLAG.HIDDEN)
    charge_shadow.set_style_text_font(lv.font_montserrat_16, 0)
    charge = lv.label(root)
    charge.set_text(lv.SYMBOL.CHARGE)
    charge.set_style_text_color(lv.color_hex(0x0091B3), 0)
    charge.align_to(icon, lv.ALIGN.CENTER, 0, 1)
    charge.add_flag(lv.obj.FLAG.HIDDEN)
    charge.set_style_text_font(lv.font_montserrat_12, 0)

    # Counter to flash charging symbol
    charge_flash_counter = 0
    # -----------------------------
    # Update logic
    # -----------------------------
    def update():
        nonlocal charge_flash_counter
        
        pct = int(var.system_data.bat_percentage)
        charging = bool(var.system_data.usb_connected)

        # Select icon level
        if pct <= 10:
            symbol = lv.SYMBOL.BATTERY_EMPTY
        elif pct <= 30:
            symbol = lv.SYMBOL.BATTERY_1
        elif pct <= 60:
            symbol = lv.SYMBOL.BATTERY_2
        elif pct <= 85:
            symbol = lv.SYMBOL.BATTERY_3
        else:
            symbol = lv.SYMBOL.BATTERY_FULL

        icon.set_text(symbol)

        # Color logic
        if pct <= 20:
            color = lv.color_hex(0x303BFF)
        else:
            color = lv.color_hex(0x666666)

        icon.set_style_text_color(color, 0)

        # Charging icon
        if charging and charge_flash_counter % 2 == 0:
            charge.remove_flag(lv.obj.FLAG.HIDDEN)
            charge_shadow.remove_flag(lv.obj.FLAG.HIDDEN)
        else:
            charge.add_flag(lv.obj.FLAG.HIDDEN)
            charge_shadow.add_flag(lv.obj.FLAG.HIDDEN)
            
        charge_flash_counter += 1

    return {
        "root": root,
        "icon": icon,
        "charge": charge,
        "update": update,
    }

def create_dummy_screen(alt=False):
    
    lv = init()
    
    scr = lv.obj()

    # Background color
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)

    # Simple slider and label in the middle
    slider = lv.slider(scr)
    slider.set_size(180, 50)
    slider.center()
    
    label = lv.label(scr)
    label.set_text('HELLO WORLD!')
    label.align(lv.ALIGN.CENTER, 0, -50)

    # Enable swipe on the full screen
    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Dummy"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)
    
    #lv.screen_load(scr)
    
    return scr

def create_roll_indicator_screen(alt=False):

    lv = init()

    scr = lv.obj()

    # Black background
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)

    # Screen constants
    CENTER_X = 120
    CENTER_Y = 120
    LINE_LEN = 220

    # How far the pitch dot can move from center
    PITCH_RANGE_PX = 90
    DOT_SIZE = 24

    # =========================
    # Horizon line
    # =========================

    line = lv.line(scr)

    style = lv.style_t()
    style.init()

    style.set_line_color(lv.color_hex(0x00FF00))
    style.set_line_width(3)

    line.add_style(style, 0)

    points = [
        {"x": 0, "y": 0},
        {"x": 0, "y": 0},
    ]

    line.set_points(points, 2)

    # =========================
    # Pitch indicator dot
    # =========================
    pitch_dot = lv.obj(scr)
    pitch_dot.set_size(DOT_SIZE, DOT_SIZE)
    pitch_dot.set_style_radius(DOT_SIZE // 2, 0)
    pitch_dot.set_style_bg_color(lv.color_hex(0x0000FF), 0)
    pitch_dot.set_style_bg_opa(lv.OPA.COVER, 0)
    pitch_dot.set_style_border_width(0, 0)
    pitch_dot.set_style_outline_width(0, 0)
    pitch_dot.set_style_shadow_width(0, 0)
    pitch_dot.set_style_pad_all(0, 0)

    # =========================
    # Roll label
    # =========================

    roll_lbl = lv.label(scr)
    roll_lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    roll_lbl.align(lv.ALIGN.TOP_MID, 0, 15)

    # =========================
    # Pitch label
    # =========================

    pitch_lbl = lv.label(scr)
    pitch_lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    pitch_lbl.align(lv.ALIGN.BOTTOM_MID, 0, -15)

    # =========================
    # Update function
    # =========================

    def update_screen():

        roll = var.sensor_data.rpy[0]
        pitch = var.sensor_data.rpy[1]

        # -------- Roll horizon line --------
        angle_rad = math.radians(roll)

        half_len = LINE_LEN // 2

        dx = int(math.cos(angle_rad) * half_len)
        dy = int(math.sin(angle_rad) * half_len)

        points[0]["x"] = CENTER_X - dx
        points[0]["y"] = CENTER_Y - dy

        points[1]["x"] = CENTER_X + dx
        points[1]["y"] = CENTER_Y + dy

        line.set_points(points, 2)

        # -------- Pitch dot --------
        # Clamp pitch to -90..90
        if pitch > 90:
            pitch_clamped = 90
        elif pitch < -90:
            pitch_clamped = -90
        else:
            pitch_clamped = pitch

        # +90 moves up, -90 moves down
        dot_y = CENTER_Y - int((pitch_clamped / 90.0) * PITCH_RANGE_PX)
        pitch_dot.set_pos(
            CENTER_X - DOT_SIZE // 2,
            dot_y - DOT_SIZE // 2
        )

        # -------- Labels --------
        roll_lbl.set_text("ROLL: %.1f°" % roll)
        pitch_lbl.set_text("PITCH: %.1f°" % pitch)

    # Initial draw
    update_screen()

    # Periodic update timer
    def timer_cb(timer):
        update_screen()

    lv.timer_create(timer_cb, 100, None)

    # Swipe gestures
    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Roll"

    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr

def create_sensor_screen(alt=False):
    lv = init()

    scr = lv.obj()
    scr.set_size(240, 240)
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)
    scr.set_style_border_width(0, 0)
    scr.remove_flag(lv.obj.FLAG.SCROLLABLE)

    # -----------------------------
    # Helpers
    # -----------------------------
    def make_label(parent, text, x, y, color=0xFFFFFF, font=None):
        
        lbl = lv.label(parent)
        lbl.set_text(text)
        lbl.set_style_text_color(lv.color_hex(color), 0)
        lbl.set_style_text_line_space(0, 0)
        lbl.set_style_text_letter_space(0, 0)
        lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        lbl.set_style_pad_all(0, 0)
        lbl.remove_flag(lv.obj.FLAG.SCROLLABLE)
        
        if font is not None:
            lbl.set_style_text_font(font, 0)
            
        lbl.align(lv.ALIGN.CENTER, x, y)
        return lbl

    def set_arc_style(arc):
        arc.remove_style_all()
        arc.set_size(240, 240)
        arc.center()
        arc.remove_flag(lv.obj.FLAG.CLICKABLE)
        arc.remove_flag(lv.obj.FLAG.SCROLLABLE)

        # Hide background arc completely
        arc.set_style_arc_opa(lv.OPA.TRANSP, lv.PART.MAIN)

        # Hide knob
        arc.set_style_opa(lv.OPA.TRANSP, lv.PART.KNOB)

        # Indicator arc style
        arc.set_style_arc_width(10, lv.PART.INDICATOR)
        arc.set_style_arc_rounded(True, lv.PART.INDICATOR)
        arc.set_style_arc_color(lv.color_hex(0x00FF00), lv.PART.INDICATOR)

    def sensor_color_co2(co2):
        if co2 < 1000:
            var.led_request_co2 = "Green"
            return lv.color_hex(0x55FF00)   # green
        elif co2 < 1500:
            var.led_request_co2 = "Yellow"
            return lv.color_hex(0x00D0FF)   # yellow
        else:
            var.led_request_co2 = "Red"
            return lv.color_hex(0x303BFF)   # red

    def sensor_color_temp(temp):
        if temp < 18:
            var.led_request_temp = "Blue"
            return lv.color_hex(0xFF9933)   # blue-ish
        elif temp < 26:
            var.led_request_temp = "Green"
            return lv.color_hex(0x55FF00)   # green
        elif temp < 30:
            var.led_request_temp = "Yellow"
            return lv.color_hex(0x00D0FF)   # yellow
        else:
            var.led_request_temp = "Red"
            return lv.color_hex(0x303BFF)   # red

    def sensor_color_hum(hum):
        if hum < 30:
            var.led_request_hum = "Yellow"
            return lv.color_hex(0x00D0FF)   # dry -> yellow
        elif hum <= 60:
            var.led_request_hum = "Green"
            return lv.color_hex(0x55FF00)   # good -> green
        else:
            var.led_request_hum = "Red"
            return lv.color_hex(0x303BFF)   # too humid -> red

    # -----------------------------
    # Separator lines (120° apart)
    # -----------------------------
    sep_color = lv.color_hex(0x303030)

    # Coordinates chosen for a 240x240 round display
    # Center is (120,120)
    # One separator goes upward, the other two downward-left/downward-right
    line_style = lv.style_t()
    line_style.init()
    line_style.set_line_color(sep_color)
    line_style.set_line_width(2)
    line_style.set_line_rounded(True)

    # top separator
    line1_points = [
        {"x": 120, "y": 120},
        {"x": 33, "y": 70},
    ]
    line1 = lv.line(scr)
    line1.set_points(line1_points, len(line1_points))
    line1.add_style(line_style, 0)

    # bottom-left separator
    line2_points = [
        {"x": 120, "y": 120},
        {"x": 207, "y": 70},
    ]
    line2 = lv.line(scr)
    line2.set_points(line2_points, len(line2_points))
    line2.add_style(line_style, 0)

    # bottom-right separator
    line3_points = [
        {"x": 120, "y": 120},
        {"x": 120, "y": 220},
    ]
    line3 = lv.line(scr)
    line3.set_points(line3_points, len(line3_points))
    line3.add_style(line_style, 0)

    # -----------------------------
    # Edge arcs
    # -----------------------------
    # Using 3 separate arcs with small gaps so they don't touch.
    # Segment centers:
    #   CO2       -> around 270°
    #   TEMP      -> around 150°
    #   HUMIDITY  -> around 30°
    # In LVGL angles:
    #   0° = right, 90° = bottom, 180° = left, 270° = top
    # So top is 240..300 roughly, bottom-left 120..180, bottom-right 0..60
    # with gaps between them.

    arc_co2 = lv.arc(scr)
    set_arc_style(arc_co2)
    arc_co2.set_rotation(0)
    arc_co2.set_bg_angles(0, 360)
    arc_co2.set_angles(215, 325)

    arc_temp = lv.arc(scr)
    set_arc_style(arc_temp)
    arc_temp.set_rotation(0)
    arc_temp.set_bg_angles(0, 360)
    arc_temp.set_angles(102, 205)

    arc_hum = lv.arc(scr)
    set_arc_style(arc_hum)
    arc_hum.set_rotation(0)
    arc_hum.set_bg_angles(0, 360)
    arc_hum.set_angles(335, 78)

    # -----------------------------
    # Labels
    # -----------------------------
    # Titles
    co2_title  = make_label(scr, "CO2",    0, -90, 0x808080)
    temp_title = make_label(scr, "TEMP", -42,   2, 0x808080)
    hum_title  = make_label(scr, "HUM",   45,   2, 0x808080)

    # Values
    co2_value  = make_label(scr, "--",     0, -52, 0xFFFFFF, font=lv.font_montserrat_48)
    co2_unit   = make_label(scr, "ppm",    0, -20, 0x707070)

    temp_value = make_label(scr, "--",   -46,  38, 0xFFFFFF, font=lv.font_montserrat_40)
    temp_unit  = make_label(scr, "°C",   -25,  85, 0x707070)

    hum_value  = make_label(scr, "--",    48,  38, 0xFFFFFF, font=lv.font_montserrat_40)
    hum_unit   = make_label(scr, "%",     25,  85, 0x707070)

    # -----------------------------
    # Battery widget
    # -----------------------------
    bat = create_battery_widget(scr, 0, 111, font = lv.font_montserrat_16)

    # -----------------------------
    # Refresh callback
    # -----------------------------
    def refresh_cb(timer):
        try:
            co2 = int(var.sensor_data.co2_scd41)
        except:
            co2 = 0

        try:
            temp = float(var.sensor_data.temp_scd41)
        except:
            temp = 0.0

        try:
            hum = float(var.sensor_data.humidity_scd41)
        except:
            hum = 0.0

        co2_value.set_text(str(co2))
        temp_value.set_text("{:.1f}".format(temp))
        hum_value.set_text("{:.0f}".format(hum))

        # Realign because text width changes
        #co2_value.align(lv.ALIGN.CENTER, 0, -35)
        #co2_unit.align(lv.ALIGN.CENTER, 0, -8)

        #temp_value.align(lv.ALIGN.CENTER, -60, 78)
        #temp_unit.align(lv.ALIGN.CENTER, -60, 102)

        #hum_value.align(lv.ALIGN.CENTER, 60, 78)
        #hum_unit.align(lv.ALIGN.CENTER, 60, 102)
        
        arc_co2.set_style_arc_color(sensor_color_co2(co2), lv.PART.INDICATOR)
        arc_temp.set_style_arc_color(sensor_color_temp(temp), lv.PART.INDICATOR)
        arc_hum.set_style_arc_color(sensor_color_hum(hum), lv.PART.INDICATOR)
        
        bat["update"]()

    # Initial refresh
    refresh_cb(None)

    # Refresh every second
    lv.timer_create(refresh_cb, 3000, None)

    # Enable swipe on the full screen
    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Sensors"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr

def create_ap_screen(alt=False):

    lv = init()

    scr = lv.obj()
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.remove_flag(lv.obj.FLAG.SCROLLABLE)

    # Title
    title = lv.arclabel(scr)
    title.set_size(240, 240)
    title.center()
    title.set_text("ACCESS POINT")
    title.set_style_text_font(lv.font_montserrat_14, 0)
    title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    title.set_radius(100)
    title.set_angle_start(245)
    title.set_angle_size(110)

    # Big button
    btn_ap = lv.obj(scr)
    btn_ap.set_size(180, 90)
    btn_ap.align(lv.ALIGN.CENTER, 0, 0)
    btn_ap.add_flag(lv.obj.FLAG.CLICKABLE)
    btn_ap.remove_flag(lv.obj.FLAG.SCROLLABLE)
    btn_ap.set_style_radius(18, 0)
    btn_ap.set_style_pad_all(0, 0)
    btn_ap.set_style_border_width(0, 0)

    btn_label = lv.label(btn_ap)
    btn_label.set_text("ACTIVATE AP")
    btn_label.set_style_text_font(lv.font_montserrat_24, 0)
    btn_label.center()

    # Deactivation label
    label = lv.label(scr)
    label.set_text(" ")
    label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    label.align(lv.ALIGN.CENTER, 0, 70)

    # Visual state updater
    def update_button_state():
        if not var.ap_request:
            btn_ap.add_flag(lv.obj.FLAG.CLICKABLE)
            btn_ap.set_style_bg_color(lv.color_hex(0x404040), 0)
            btn_ap.set_style_bg_opa(lv.OPA.COVER, 0)
            btn_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
            label.set_text(" ")
        else:
            btn_ap.remove_flag(lv.obj.FLAG.CLICKABLE)
            btn_ap.set_style_bg_color(lv.color_hex(0x181818), 0)
            btn_ap.set_style_bg_opa(lv.OPA.COVER, 0)
            btn_label.set_style_text_color(lv.color_hex(0x606060), 0)
            label.set_text("Auto disable in " + str(int(var.ap_disable_timer)) + "s")

    # Button callback
    def ap_btn_cb(e):
        var.ap_request = True

    btn_ap.add_event_cb(ap_btn_cb, lv.EVENT.CLICKED, None)

    # Periodic checker
    def ap_timer_cb(timer):
        try:
            update_button_state()
        except Exception as e:
            print("AP timer error:", e)

    ap_timer = lv.timer_create(ap_timer_cb, 2000, None)

    # Initial state
    update_button_state()

    # Swipe support
    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Acces Point"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr

def create_timezone_screen(alt=False):
    
    lv = init()
    
    scr = lv.obj()
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)

    # -----------------------------
    # Helpers
    # -----------------------------
    def get_hours():
        return int(var.TZ_OFFSET // 3600)

    def set_hours(h):
        var.audio_events.put_nowait(var.EVENT_AUDIO_SHORT)
        
        if h < -12:
            h = -12
        if h > 14:
            h = 14

        seconds = h * 3600
        var.TZ_OFFSET = seconds
        
        # -----------------------------
        # Update persistent_config.py
        # -----------------------------
        try:
            with open("persistent_config.py", "r") as f:
                lines = f.readlines()

            new_lines = []
            found = False

            for line in lines:
                if line.strip().startswith("TZ_OFFSET"):
                    new_lines.append("TZ_OFFSET = {}\n".format(seconds))
                    found = True
                else:
                    new_lines.append(line)

            # If not found, append it (safety)
            if not found:
                new_lines.append("\nTZ_OFFSET = {}\n".format(seconds))

            with open("persistent_config.py", "w") as f:
                f.write("".join(new_lines))

        except Exception as e:
            print("Config write error:", e)
        
        update_label()

    def update_label():
        h = get_hours()
        sign = "+" if h >= 0 else ""
        label.set_text("UTC {}{}".format(sign, h))

    # Curved title
    title = lv.arclabel(scr)
    title.set_size(240, 240)
    title.center()
    title.set_text("TIME ZONE")
    title.set_style_text_font(lv.font_montserrat_14, 0)
    title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)

    # These are the key arc-label controls in LVGL 9.x
    title.set_radius(100)         # curve radius
    title.set_angle_start(250)    # where text begins
    title.set_angle_size(100)     # span of the text

    # Center label
    label = lv.label(scr)
    label.set_style_text_font(lv.font_montserrat_34, 0)
    label.align(lv.ALIGN.TOP_MID, 0, 110)

    # + BUTTON (top)
    btn_plus = lv.obj(scr)
    btn_plus.set_size(100, 60)
    btn_plus.align(lv.ALIGN.TOP_MID, 0, 40)

    # Make it look like a button
    btn_plus.set_style_bg_color(lv.color_hex(0x333333), 0)
    btn_plus.set_style_radius(10, 0)

    label_plus = lv.label(btn_plus)
    label_plus.set_text("+")
    label_plus.set_style_text_font(lv.font_montserrat_32, 0)
    label_plus.center()

    def plus_cb(e):
        set_hours(get_hours() + 1)

    btn_plus.add_event_cb(plus_cb, lv.EVENT.CLICKED, None)

    # - BUTTON (bottom)
    btn_minus = lv.obj(scr)
    btn_minus.set_size(100, 60)
    btn_minus.align(lv.ALIGN.BOTTOM_MID, 0, -20)

    btn_minus.set_style_bg_color(lv.color_hex(0x333333), 0)
    btn_minus.set_style_radius(10, 0)

    label_minus = lv.label(btn_minus)
    label_minus.set_text("-")
    label_minus.set_style_text_font(lv.font_montserrat_32, 0)
    label_minus.center()

    def minus_cb(e):
        set_hours(get_hours() - 1)

    btn_minus.add_event_cb(minus_cb, lv.EVENT.CLICKED, None)

    btn_plus.remove_flag(lv.obj.FLAG.SCROLLABLE)
    btn_minus.remove_flag(lv.obj.FLAG.SCROLLABLE)

    # Make the buttons clickable
    btn_plus.add_flag(lv.obj.FLAG.CLICKABLE)
    btn_minus.add_flag(lv.obj.FLAG.CLICKABLE)

    # Init label
    update_label()

    # Swipe
    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Timezone"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr

def create_co2_screen(alt=False):
    lv = init()

    scr = lv.obj()
    scr.set_size(240, 240)
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)
    scr.set_style_border_width(0, 0)
    scr.remove_flag(lv.obj.FLAG.SCROLLABLE)

    # -----------------------------
    # Ring with fake radial gradient
    # -----------------------------
    def make_ring(size, width, color, opa):
        a = lv.arc(scr)
        a.remove_style_all()
        a.remove_flag(lv.obj.FLAG.CLICKABLE)
        a.set_size(size, size)
        a.align(lv.ALIGN.CENTER, 0, 0)
        a.set_rotation(270)
        a.set_bg_angles(0, 360)
        a.set_range(0, 100)
        a.set_value(100)
        a.set_style_pad_all(0, 0)

        # hide background part
        a.set_style_arc_width(0, lv.PART.MAIN)
        a.set_style_arc_opa(lv.OPA.TRANSP, lv.PART.MAIN)

        # visible full ring
        a.set_style_arc_width(width, lv.PART.INDICATOR)
        a.set_style_arc_color(color, lv.PART.INDICATOR)
        a.set_style_arc_opa(opa, lv.PART.INDICATOR)
        return a

    # Main glow
    ring_g1 = make_ring(236, 6, lv.color_hex(0x00FF55), 56)
    # Soft bloom
    ring_g2 = make_ring(225, 8, lv.color_hex(0x00FF55), 36)
    # Deep ambient glow
    ring_g3 = make_ring(208, 14, lv.color_hex(0x00FF55), 24)

    # main sharp ring
    ring = lv.arc(scr)
    ring.remove_style_all()
    ring.remove_flag(lv.obj.FLAG.CLICKABLE)
    ring.set_size(240, 240)
    ring.align(lv.ALIGN.CENTER, 0, 0)
    ring.set_rotation(270)
    ring.set_bg_angles(0, 360)
    ring.set_range(0, 100)
    ring.set_value(100)
    ring.set_style_pad_all(0, 0)

    ring.set_style_arc_width(2, lv.PART.MAIN)
    ring.set_style_arc_color(lv.color_hex(0x103810), lv.PART.MAIN)
    ring.set_style_arc_opa(lv.OPA.COVER, lv.PART.MAIN)

    ring.set_style_arc_width(2, lv.PART.INDICATOR)
    ring.set_style_arc_color(lv.color_hex(0x00FF55), lv.PART.INDICATOR)
    ring.set_style_arc_opa(lv.OPA.COVER, lv.PART.INDICATOR)

    # -----------------------------
    # Big CO2 number
    # -----------------------------
    co2_label = lv.label(scr)
    co2_label.set_text("69")
    co2_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    co2_label.set_style_text_font(lv.montserrat_96, 0)
    co2_label.center()
    co2_label.align(lv.ALIGN.CENTER, 0, 0)

    # -----------------------------
    # ppm text
    # -----------------------------
    ppm_label = lv.label(scr)
    ppm_label.set_text("ppm")
    ppm_label.set_style_text_color(lv.color_hex(0x00FF55), 0)
    ppm_label.set_style_text_font(lv.font_montserrat_20, 0)
    ppm_label.align(lv.ALIGN.CENTER, 0, 60)

    # -----------------------------
    # Title
    # -----------------------------
    title_label = lv.label(scr)
    title_label.set_text("CO2")
    title_label.set_style_text_color(lv.color_hex(0x888888), 0)
    title_label.set_style_text_font(lv.font_montserrat_16, 0)
    title_label.align(lv.ALIGN.CENTER, 0, -75)

    # -----------------------------
    # Battery widget
    # -----------------------------
    bat = create_battery_widget(scr, 0, 87, font = lv.font_montserrat_16)
    
    # -----------------------------
    # Breathing animation
    # -----------------------------
    BREATH_OPA = [0, 2, 5, 9, 15, 22, 30, 37, 40, 37, 30, 22, 15, 9, 5, 2]

    glow_state = {"i": 0}

    def glow_timer_cb(t):
        x = BREATH_OPA[glow_state["i"]]

        ring_g1.set_style_arc_opa(45 + x, lv.PART.INDICATOR)
        #ring_g2.set_style_arc_opa(14 + (x * 2) // 3, lv.PART.INDICATOR)

        glow_state["i"] = (glow_state["i"] + 1) % len(BREATH_OPA)

    #lv.timer_create(glow_timer_cb, 1000, None)

    # -----------------------------
    # CO2 update
    # -----------------------------
    state = {
        "co2": None,
        "color_key": None,
    }
    
    def set_co2_cb(t):
        value = int(var.sensor_data.co2_scd41)

        if value < 1000:
            color_key = 0
            color = lv.color_hex(0x00FF55)
        elif value < 1500:
            color_key = 1
            color = lv.color_hex(0x00D0FF)
        else:
            color_key = 2
            color = lv.color_hex(0x303BFF)
            
        # Update text only if CO2 value changed
        if value != state["co2"]:
            state["co2"] = value
            co2_label.set_text(str(value))

        # Update colors only if color category changed
        if color_key != state["color_key"]:
            state["color_key"] = color_key

            ring.set_style_arc_color(color, lv.PART.INDICATOR)
            ppm_label.set_style_text_color(color, 0)

            ring_g1.set_style_arc_color(color, lv.PART.INDICATOR)
            ring_g2.set_style_arc_color(color, lv.PART.INDICATOR)
            ring_g3.set_style_arc_color(color, lv.PART.INDICATOR)
        
        bat["update"]()

    lv.timer_create(set_co2_cb, 3000, None)

    # Enable swipe on full screen
    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "CO2"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr

def co2_chart_draw_event_cb(e):
    lv = init()

    draw_task = e.get_draw_task()
    if draw_task is None:
        return

    if draw_task.get_type() != lv.DRAW_TASK_TYPE.LINE:
        return

    line_dsc = draw_task.get_line_dsc()
    if line_dsc is None:
        return

    # Debug once if needed
    # print("part:", line_dsc.base.part)

    if line_dsc.base.part == lv.PART.ITEMS:
        _add_faded_area(e, line_dsc)

    elif line_dsc.base.part == lv.PART.MAIN:
        pass
        # optional: customize grid lines here later

def _add_faded_area(e, line_dsc):
    lv = init()

    obj = e.get_target_obj()

    coords = lv.area_t()
    obj.get_coords(coords)

    p1 = line_dsc.p1
    p2 = line_dsc.p2
    color = line_dsc.color
    layer = line_dsc.base.layer

    x_left = int(min(p1.x, p2.x))
    x_right = int(max(p1.x, p2.x)) - 1
    y_top = int(min(p1.y, p2.y))
    y_low = int(max(p1.y, p2.y))
    y_bottom = int(coords.y2)

    if x_right < x_left:
        x_right = x_left

    chart_top = int(coords.y1)
    chart_h = int(coords.y2 - coords.y1)
    if chart_h <= 0:
        return

    def y_to_opa(y):
        # Stronger near top, weaker near bottom
        rel = (y - chart_top) / chart_h
        if rel < 0:
            rel = 0
        if rel > 1:
            rel = 1

        # map top->bottom : 0.60 -> 0.00 approximately
        opa = int(153 * (1.0 - rel))   # 153 ~= 60%
        if opa < 0:
            opa = 0
        if opa > 255:
            opa = 255
        return opa

    opa_top = y_to_opa(y_top)
    opa_low = y_to_opa(y_low)
    opa_bottom = y_to_opa(y_bottom)

    # -------------------------
    # Triangle wedge
    # -------------------------
    tri_dsc = lv.draw_triangle_dsc_t()
    tri_dsc.init()

    tri_dsc.grad.dir = lv.GRAD_DIR.VER
    tri_dsc.grad.stops_count = 2
    tri_dsc.grad.stops = [
        lv.grad_stop_t({
            'color': color,
            'opa': opa_top,
            'frac': 0
        }),
        lv.grad_stop_t({
            'color': color,
            'opa': opa_low,
            'frac': 0xFF
        })
    ]

    pt0 = lv.point_precise_t()
    pt0.x = int(p1.x)
    pt0.y = int(p1.y)

    pt1 = lv.point_precise_t()
    pt1.x = int(p2.x)
    pt1.y = int(p2.y)

    pt2 = lv.point_precise_t()
    if p1.y > p2.y:
        pt2.x = int(p2.x)
        pt2.y = int(p1.y)
    else:
        pt2.x = int(p1.x)
        pt2.y = int(p2.y)

    tri_dsc.p = [pt0, pt1, pt2]

    lv.draw_triangle(layer, tri_dsc)

    # -------------------------
    # Rectangle below
    # -------------------------
    rect_dsc = lv.draw_rect_dsc_t()
    rect_dsc.init()
    rect_dsc.bg_color = color
    rect_dsc.bg_opa = opa_low
    rect_dsc.border_opa = lv.OPA.TRANSP
    rect_dsc.radius = 0
        
    rect_dsc.bg_grad.dir = lv.GRAD_DIR.VER
    rect_dsc.bg_grad.stops_count = 2
    rect_dsc.bg_grad.stops = [
        lv.grad_stop_t({
            'color': color,
            'opa': lv.OPA.COVER,
            'frac': 0
        }),
        lv.grad_stop_t({
            'color': color,
            'opa': lv.OPA._10,
            'frac': 0xFF
        })
    ]

    rect_area = lv.area_t()
    rect_area.x1 = x_left
    rect_area.x2 = x_right
    rect_area.y1 = y_low
    rect_area.y2 = y_bottom

    lv.draw_rect(layer, rect_dsc, rect_area)

def create_co2_chart_screen(alt=False):
    lv = init()

    scr = lv.obj()
    scr.set_size(240, 240)
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)
    scr.set_style_border_width(0, 0)
    scr.remove_flag(lv.obj.FLAG.SCROLLABLE)

    # Chart
    chart = lv.chart(scr)
    chart.set_size(240, 240)
    #chart.center()
    chart.align(lv.ALIGN.CENTER, 0, 0)
    
    chart.remove_flag(lv.obj.FLAG.CLICKABLE)
    chart.remove_flag(lv.obj.FLAG.SCROLLABLE)
    chart.remove_flag(lv.obj.FLAG.GESTURE_BUBBLE)

    # Make chart background slightly gray first so we can see it exists
    chart.set_style_bg_color(lv.color_hex(0x000000), 0)
    chart.set_style_bg_opa(lv.OPA.COVER, 0)
    chart.set_style_border_width(1, 0)
    chart.set_style_border_color(lv.color_hex(0x000000), 0)
    chart.set_style_pad_all(0, 0)

    # Line chart
    chart.set_type(lv.chart.TYPE.LINE)
    chart.set_update_mode(lv.chart.UPDATE_MODE.SHIFT)
    
    # Change marker size to 0
    chart.set_style_size(0, 0, lv.PART.INDICATOR)

    # Grid lines
    chart.set_div_line_count(5, 5)
    chart.set_style_line_color(lv.color_hex(0x606060), lv.PART.MAIN)
    chart.set_style_line_opa(lv.OPA._50, lv.PART.MAIN)
    chart.set_style_line_width(1, lv.PART.MAIN)
    chart.set_style_line_dash_width(4, lv.PART.MAIN)
    chart.set_style_line_dash_gap(4, lv.PART.MAIN)
    
    # Y range
    chart.set_axis_range(lv.chart.AXIS.PRIMARY_Y, 300, 1000)
    ser = chart.add_series(lv.color_hex(0x00ff66), lv.chart.AXIS.PRIMARY_Y)

    # X axis labels
    label_x_1 = lv.label(chart)
    label_x_1.set_text("-1h")
    label_x_1.set_style_text_color(lv.color_hex(0x606060), 0)
    label_x_1.set_style_bg_color(lv.color_hex(0x000000), 0)
    label_x_1.set_style_bg_opa(lv.OPA._40, 0)
    label_x_1.set_style_pad_all(0, 1)
    label_x_1.align(lv.ALIGN.TOP_MID, 58, 204)
    label_x_2 = lv.label(chart)
    label_x_2.set_text("-2h")
    label_x_2.set_style_text_color(lv.color_hex(0x606060), 0)
    label_x_2.set_style_bg_color(lv.color_hex(0x000000), 0)
    label_x_2.set_style_bg_opa(lv.OPA._40, 0)
    label_x_2.set_style_pad_all(0, 1)
    label_x_2.align(lv.ALIGN.TOP_MID, -3, 220)
    label_x_3 = lv.label(chart)
    label_x_3.set_text("-3h")
    label_x_3.set_style_text_color(lv.color_hex(0x606060), 0)
    label_x_3.set_style_bg_color(lv.color_hex(0x000000), 0)
    label_x_3.set_style_bg_opa(lv.OPA._40, 0)
    label_x_3.set_style_pad_all(0, 1)
    label_x_3.align(lv.ALIGN.TOP_MID, -64, 204)
    
    # Y axis labels
    label_y_1 = lv.label(chart)
    label_y_1.set_text("600")
    label_y_1.set_style_text_color(lv.color_hex(0x606060), 0)
    label_y_1.set_style_bg_color(lv.color_hex(0x000000), 0)
    label_y_1.set_style_bg_opa(lv.OPA._40, 0)
    label_y_1.set_style_pad_all(1, 0)
    label_y_1.align(lv.ALIGN.TOP_MID, -85, 49)
    label_y_2 = lv.label(chart)
    label_y_2.set_text("400")
    label_y_2.set_style_text_color(lv.color_hex(0x606060), 0)
    label_y_2.set_style_bg_color(lv.color_hex(0x000000), 0)
    label_y_2.set_style_bg_opa(lv.OPA._40, 0)
    label_y_2.set_style_pad_all(1, 0)
    label_y_2.align(lv.ALIGN.TOP_MID, -85, 170)
        
    # Title just so we know screen loaded
    label = lv.label(scr)
    label.set_text("CO2 ppm")
    label.set_style_text_color(lv.color_hex(0x00ff66), 0)
    label.align(lv.ALIGN.TOP_MID, 0, 8)
    
    def update_co2_chart(timer):
        
        value = int(var.sensor_data.co2_scd41)
        
        if value < 1000:
            color = lv.color_hex(0x55FF00)
        elif value < 1500:
            color = lv.color_hex(0x00D0FF)
        else:
            color = lv.color_hex(0x303BFF)

        txt = str(value)
        label.set_text(txt + " ppm")
        label.set_style_text_color(color, 0)

        display_data = []
        if len(var.scd41_co2_history) < var.scd41_co2_max_display_history:
            display_data = (var.scd41_co2_max_display_history - len(var.scd41_co2_history)) * [var.scd41_co2_history[0]]
            display_data += var.scd41_co2_history
        elif len(var.scd41_co2_history) == var.scd41_co2_max_display_history:
            display_data = var.scd41_co2_history
        else:
            display_data = var.scd41_co2_history[-var.scd41_co2_max_display_history:]

        #print("source history len", len(var.scd41_co2_history))
        #print("source history last", var.scd41_co2_history[-1])
        #print("showed history len:", len(display_data))
        #print("showed history last:", display_data[-1])
        # Make LVGL series length follow your list length
        chart.set_point_count(len(display_data))

        # Optional: dynamic Y range based on actual data
        y_min = min(display_data) - 50
        y_max = max(display_data) + 50

        # Avoid zero-height range
        if y_min == y_max:
            y_min -= 50
            y_max += 50
            if y_min < 0:
                y_min = 0
                                
        # Or comment this out to stick to fixed 0…3000 range above
        chart.set_axis_range(lv.chart.AXIS.PRIMARY_Y, y_min, y_max)
        
        # Update Y labels
        label_y_1.set_text(str(int((y_max - (y_max - y_min)/4)/10)*10))
        label_y_2.set_text(str(int((y_min + (y_max - y_min)/4)/10)*10))

        # Fill the backing array directly
        y_points = chart.get_series_y_array(ser)
        for i, v in enumerate(display_data):
            y_points[i] = v

        chart.refresh()
        
    lv.timer_create(update_co2_chart, 3000, None)
    
    # Faded area below chart looks great but kills asyncio tasks
    #chart.add_event_cb(co2_chart_draw_event_cb, lv.EVENT.DRAW_TASK_ADDED, None)
    #chart.add_flag(lv.obj.FLAG.SEND_DRAW_TASK_EVENTS)

    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "CO2 chart"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr

def create_sensor_table(alt=False):
    lv = init()
    scr = lv.obj()

    # --- Screen style / remove default paddings ---
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)
    scr.set_style_text_color(lv.color_hex(0xffffff), 0)

    # Kill theme padding on the root screen
    scr.set_style_pad_top(0, 0)
    scr.set_style_pad_bottom(0, 0)
    scr.set_style_pad_left(0, 0)
    scr.set_style_pad_right(0, 0)

    # This will be the *only* scrollable area
    page = lv.obj(scr)
    page.set_size(SCREEN_W, SCREEN_H)
    page.align(lv.ALIGN.TOP_LEFT, 0, 0)

    # Remove padding/margins that push content down/right
    page.set_style_pad_top(50, 0)
    page.set_style_pad_bottom(0, 0)
    page.set_style_pad_left(0, 0)
    page.set_style_pad_right(0, 0)
    page.set_style_border_width(0, 0)
    page.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN)
    page.set_style_bg_opa(lv.OPA.COVER, lv.PART.MAIN)

    # ✅ Only vertical scrolling on the page (no horizontal)
    page.set_scroll_dir(lv.DIR.VER)
    page.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

    table = lv.table(page)
    table.set_size(SCREEN_W, 24*30+100)
    table.align(lv.ALIGN.TOP_LEFT, 0, 0)

    # ✅ Make sure table itself does NOT scroll -> removes 2nd scrollbar
    table.remove_flag(lv.obj.FLAG.SCROLLABLE)
    table.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

    # (Optional but helps: remove table internal padding so it sits tighter)
    table.set_style_pad_top(0, 0)
    table.set_style_pad_bottom(0, 0)
    table.set_style_pad_left(0, 0)
    table.set_style_pad_right(0, 0)

    # tighter table cells
    table.set_style_pad_left(5, lv.PART.ITEMS)
    table.set_style_pad_right(0, lv.PART.ITEMS)
    table.set_style_pad_top(8, lv.PART.ITEMS)
    table.set_style_pad_bottom(8, lv.PART.ITEMS)

    # optional: align text tighter
    table.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.ITEMS)

    # 3 columns and 18 rows
    table.set_column_count(3)
    table.set_row_count(24)

    table.set_column_width(0, 10)
    table.set_column_width(1, 110)
    table.set_column_width(2, 120)

    # Static labels
    table.set_cell_value(0, 1, "Temp [°C]")
    table.set_cell_value(1, 1, "Temp 2 [°C]")
    table.set_cell_value(2, 1, "Humidity")
    table.set_cell_value(3, 1, "CO2 [ppm]")
    table.set_cell_value(4, 1, "Lux")
    table.set_cell_value(5, 1, "Acc X")
    table.set_cell_value(6, 1, "Acc Y")
    table.set_cell_value(7, 1, "Acc Z")
    table.set_cell_value(8, 1, "Gyro X")
    table.set_cell_value(9, 1, "Gyro Y")
    table.set_cell_value(10, 1, "Gyro Z")
    table.set_cell_value(11, 1, "Battery [V]")
    table.set_cell_value(12, 1, "Battery %")
    table.set_cell_value(13, 1, "USB")
    table.set_cell_value(14, 1, "Buttons")
    table.set_cell_value(15, 1, "RTC date")
    table.set_cell_value(16, 1, "RTC time")
    table.set_cell_value(17, 1, "Local date")
    table.set_cell_value(18, 1, "Local time")
    table.set_cell_value(19, 1, "AP")
    table.set_cell_value(20, 1, "WiFi")
    table.set_cell_value(21, 1, "MQTT server")
    table.set_cell_value(22, 1, "/ storage")
    table.set_cell_value(23, 1, "RAM")
    

    # Styles
    #table.set_style_bg_color(lv.color_hex(0x101010), 0)
    table.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN)
    table.set_style_bg_color(lv.color_hex(0x000000), lv.PART.ITEMS)
    table.set_style_bg_opa(lv.OPA.COVER, lv.PART.ITEMS)
    table.set_style_text_color(lv.color_hex(0x00ff33), lv.PART.ITEMS)
    #table.set_style_text_font(lv.font_unscii_8, lv.PART.ITEMS)
    table.set_style_border_color(lv.color_hex(0x000000), lv.PART.ITEMS)
    # Remove outside borders
    table.set_style_border_width(0, lv.PART.MAIN)

    def table_update_cb(task):
        table.set_cell_value(0, 2, "{:.1f}".format(var.sensor_data.temp_scd41))
        if var.hw_variant == "i80":
            table.set_cell_value(1, 2, "{:.1f}".format(var.sensor_data.temp_qmi8658c))
        elif var.hw_variant == "spi":
            table.set_cell_value(1, 2, "{:.1f}".format(var.sensor_data.temp_ds3231))
        table.set_cell_value(2, 2, "{:.1f}".format(var.sensor_data.humidity_scd41))
        table.set_cell_value(3, 2, "{}".format(int(var.sensor_data.co2_scd41)))
        table.set_cell_value(4, 2, "{:.2f}".format(var.sensor_data.lux_veml7700))
        table.set_cell_value(5, 2, "{:.2f}".format(var.sensor_data.acc_qmi8658c[0]))
        table.set_cell_value(6, 2, "{:.2f}".format(var.sensor_data.acc_qmi8658c[1]))
        table.set_cell_value(7, 2, "{:.2f}".format(var.sensor_data.acc_qmi8658c[2]))
        table.set_cell_value(8, 2, "{:.2f}".format(var.sensor_data.gyro_qmi8658c[0]))
        table.set_cell_value(9, 2, "{:.2f}".format(var.sensor_data.gyro_qmi8658c[1]))
        table.set_cell_value(10, 2, "{:.2f}".format(var.sensor_data.gyro_qmi8658c[2]))
        table.set_cell_value(11, 2, "{:.2f}".format(var.system_data.bat_volt))
        table.set_cell_value(12, 2, "{:.1f}".format(var.system_data.bat_percentage))
        table.set_cell_value(13, 2, "{}".format(var.system_data.usb_connected))
        table.set_cell_value(14, 2, "{}".format(var.system_data.buttons))

        timestamp = var.system_data.time_rtc
        date_str = f"{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d}"
        time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
        table.set_cell_value(15, 2, date_str)
        table.set_cell_value(16, 2, time_str)


        timestamp = localtime_with_offset(var.TZ_OFFSET)
        date_str = f"{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d}"
        time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
        table.set_cell_value(17, 2, date_str)
        table.set_cell_value(18, 2, time_str)

        if var.ap_enabled:
            table.set_cell_value(19, 2, "On: {}s".format(int(var.ap_disable_timer)))
        elif var.ap_request:
            table.set_cell_value(19, 2, "Requested...")
        else:
            table.set_cell_value(19, 2, "Disabled")
            
        if var.wifi_connected:
            table.set_cell_value(20, 2, var.wifi_ip)
        elif var.ap_enabled:
            table.set_cell_value(20, 2, "Disabled")
        elif var.wifi_connecting:
            table.set_cell_value(20, 2, "Connecting...")
        elif var.wifi_sleep:
            table.set_cell_value(20, 2, "Sleep: "+str(int(var.sleep_till_next_connection)))
        else:
            table.set_cell_value(20, 2, "Disabled")

        table.set_cell_value(21, 2, var.mqqt_server_connection)

        table.set_cell_value(22, 2, "{:.1f} / {}MB".format(var.system_data.used_space_flash/1024.0, int(var.system_data.total_space_flash/1024)))
        table.set_cell_value(23, 2, "{:.1f} / {}MB".format(var.system_data.used_heap/1024.0, int(var.system_data.total_heap/1024)))

    lv.timer_create(table_update_cb, 1000, None)

    # Swipe on screen (fine)
    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Sensors"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)
    return scr

def create_snake_screen(alt=False, game=True):

    lv = init()

    scr = lv.obj()
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.remove_flag(lv.obj.FLAG.SCROLLABLE)
    
    # Curved title
    title = lv.arclabel(scr)
    title.set_size(240, 240)
    title.center()
    title.set_text(lv.SYMBOL.LEFT + "   TURN   " + lv.SYMBOL.RIGHT)
    title.set_style_text_font(lv.font_montserrat_14, 0)
    title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)

    # These are the key arc-label controls in LVGL 9.x
    title.set_radius(102)         # curve radius
    title.set_angle_start(249)    # where text begins
    title.set_angle_size(90)      # span of the text

    # Circular wall
    ring = lv.arc(scr)
    ring.remove_style_all()
    ring.remove_flag(lv.obj.FLAG.CLICKABLE)
    ring.set_size(240, 240)
    ring.align(lv.ALIGN.CENTER, 0, 0)
    ring.set_rotation(270)
    ring.set_bg_angles(0, 360)
    ring.set_range(0, 100)
    ring.set_value(100)
    ring.set_style_pad_all(0, 0)

    ring.set_style_arc_width(2, lv.PART.MAIN)
    ring.set_style_arc_color(lv.color_hex(0x103810), lv.PART.MAIN)
    ring.set_style_arc_opa(lv.OPA.COVER, lv.PART.MAIN)

    ring.set_style_arc_width(2, lv.PART.INDICATOR)
    ring.set_style_arc_color(lv.color_hex(0x888888), lv.PART.INDICATOR)
    ring.set_style_arc_opa(lv.OPA.COVER, lv.PART.INDICATOR)

    # Snake game logic
    GRID_W = 24
    GRID_H = 24
    CELL = 10

    snake = [(5, 12), (4, 12), (3, 12)]
    food = [15, 12]
    direction = [1, 0]

    cells = []

    game_w = GRID_W * CELL
    game_h = GRID_H * CELL
    offset_x = (240 - game_w) // 2
    offset_y = (240 - game_h) // 2

    green = lv.color_hex(0x00ff00)
    red = lv.color_hex(0x0000ff)

    def make_cell(color):
        o = lv.obj(scr)
        o.set_size(CELL - 1, CELL - 1)
        o.set_style_bg_color(color, 0)
        o.set_style_bg_opa(lv.OPA.COVER, 0)
        o.set_style_border_width(0, 0)
        o.remove_flag(lv.obj.FLAG.SCROLLABLE)
        return o

    food_obj = make_cell(red)

    def place_obj(o, x, y):
        o.set_pos(offset_x + x * CELL, offset_y + y * CELL)

    def draw():
        nonlocal cells

        while len(cells) < len(snake):
            cells.append(make_cell(green))

        for i, (x, y) in enumerate(snake):
            cells[i].remove_flag(lv.obj.FLAG.HIDDEN)
            place_obj(cells[i], x, y)

        for i in range(len(snake), len(cells)):
            cells[i].add_flag(lv.obj.FLAG.HIDDEN)

        place_obj(food_obj, food[0], food[1])

    def new_food():
        # Round display parameters
        cx = GRID_W * CELL // 2
        cy = GRID_H * CELL // 2
        # place foods within a smaller circle than the screen (and walls)
        radius = 100

        while True:
            gx = random.randrange(GRID_W)
            gy = random.randrange(GRID_H)

            if (gx, gy) in snake:
                continue

            # Cell center in pixels
            px = gx * CELL + CELL // 2
            py = gy * CELL + CELL // 2

            dx = px - cx
            dy = py - cy

            # Inside circle?
            if dx * dx + dy * dy <= radius * radius:
                return [gx, gy]

    def reset_game():
        nonlocal snake, food, direction
        snake = [(5, 12), (4, 12), (3, 12)]
        direction = [1, 0]
        food = new_food()
        draw()

    def snake_tick(timer):
        nonlocal snake, food

        hx, hy = snake[0]
        nx = hx + direction[0]
        ny = hy + direction[1]
        new_head = (nx, ny)
        
        # Cell center in pixels
        px = nx * CELL + CELL // 2
        py = ny * CELL + CELL // 2

        # Screen center
        cx = GRID_W * CELL // 2
        cy = GRID_H * CELL // 2
        radius = 120

        dxc = px - cx
        dyc = py - cy

        outside_circle = (
            dxc * dxc + dyc * dyc > radius * radius
        )

        if outside_circle or new_head in snake:
            reset_game()
            return

        snake.insert(0, new_head)

        if nx == food[0] and ny == food[1]:
            food = new_food()
        else:
            snake.pop()

        draw()

    def set_dir(x, y):
        if x == -direction[0] and y == -direction[1]:
            return
        direction[0] = x
        direction[1] = y
        
    def turn_left():
        dx = direction[0]
        dy = direction[1]

        # 90° CCW
        direction[0] = -dy
        direction[1] = dx

    def turn_right():
        dx = direction[0]
        dy = direction[1]

        # 90° CW
        direction[0] = dy
        direction[1] = -dx

    draw()

    snake_timer = lv.timer_create(snake_tick, 400, None)

    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Snake"
    if alt:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)
    elif game:
        var.screens_game.append(scr)
        var.screen_names_game.append(screen_name)
    else:
        var.screens.append(scr)
        var.screen_names.append(screen_name)

    return {
        "scr": scr,
        "set_dir": set_dir,
        "turn_left": turn_left,
        "turn_right": turn_right,
        "timer": snake_timer,
        "cells": cells,
        "food": food_obj,
    }