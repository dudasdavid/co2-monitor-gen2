from lv_port import init
from math import ceil
import time

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
    var.current_idx = idx % len(var.screens)
    #lv.screen_load(var.screens[var.current_idx])
    lv.screen_load_anim(
        var.screens[var.current_idx],
        lv_animation,   # animation type
        300,                             # duration in ms
        0,                               # delay in ms
        False                            # auto delete old screen
    )

def next_screen():
    lv = init()
    show_screen(var.current_idx + 1, lv.SCREEN_LOAD_ANIM.OVER_LEFT)

def prev_screen():
    lv = init()
    show_screen(var.current_idx - 1, lv.SCREEN_LOAD_ANIM.OVER_RIGHT)

def swipe_event_cb(e):
    lv = init()

    if e.get_code() != lv.EVENT.GESTURE:
        return

    indev = var.indev
    if not indev:
        return

    d = indev.get_gesture_dir()

    if d == lv.DIR.LEFT:
        next_screen()
    elif d == lv.DIR.RIGHT:
        prev_screen()


def create_co2_screen():
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

    # Inner glow layers
    ring_g1 = make_ring(250, 14, lv.color_hex(0x00FF55), 55)
    ring_g2 = make_ring(242, 18, lv.color_hex(0x00FF55), 36)
    #ring_g3 = make_ring(235, 22, lv.color_hex(0x00FF55), 24)
    #ring_g4 = make_ring(227, 26, lv.color_hex(0x00FF55), 12)

    # main sharp ring
    ring = lv.arc(scr)
    ring.remove_style_all()
    ring.remove_flag(lv.obj.FLAG.CLICKABLE)
    ring.set_size(256, 256)
    ring.align(lv.ALIGN.CENTER, 0, 0)
    ring.set_rotation(270)
    ring.set_bg_angles(0, 360)
    ring.set_range(0, 100)
    ring.set_value(100)
    ring.set_style_pad_all(0, 0)

    ring.set_style_arc_width(10, lv.PART.MAIN)
    ring.set_style_arc_color(lv.color_hex(0x103810), lv.PART.MAIN)
    ring.set_style_arc_opa(lv.OPA.COVER, lv.PART.MAIN)

    ring.set_style_arc_width(10, lv.PART.INDICATOR)
    ring.set_style_arc_color(lv.color_hex(0x00FF55), lv.PART.INDICATOR)
    ring.set_style_arc_opa(lv.OPA.COVER, lv.PART.INDICATOR)

    # -----------------------------
    # Big CO2 number
    # -----------------------------
    co2_label = lv.label(scr)
    co2_label.set_text("800")
    co2_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    co2_label.set_style_text_font(lv.montserrat_96, 0)
    co2_label.center()
    co2_label.align(lv.ALIGN.CENTER, 0, -10)

    # -----------------------------
    # ppm text
    # -----------------------------
    ppm_label = lv.label(scr)
    ppm_label.set_text("ppm")
    ppm_label.set_style_text_color(lv.color_hex(0x00FF55), 0)
    ppm_label.set_style_text_font(lv.font_montserrat_20, 0)
    ppm_label.align(lv.ALIGN.CENTER, 0, 48)

    # -----------------------------
    # Optional title
    # -----------------------------
    title_label = lv.label(scr)
    title_label.set_text("CO2")
    title_label.set_style_text_color(lv.color_hex(0x888888), 0)
    title_label.set_style_text_font(lv.font_montserrat_16, 0)
    title_label.align(lv.ALIGN.CENTER, 0, -72)

    # -----------------------------
    # Breathing animation
    # -----------------------------
    glow_state = {"opa": 0, "dir": 1}

    def glow_timer_cb(t):
        x = glow_state["opa"] + glow_state["dir"] * 6

        if x >= 40:
            x = 40
            glow_state["dir"] = -1
        elif x <= 0:
            x = 0
            glow_state["dir"] = 1

        glow_state["opa"] = x

        ring_g1.set_style_arc_opa(55 + x // 1, lv.PART.INDICATOR)
        ring_g2.set_style_arc_opa(36 + x // 2, lv.PART.INDICATOR)
        #ring_g3.set_style_arc_opa(24 + x // 3, lv.PART.INDICATOR)
        #ring_g4.set_style_arc_opa(12 + x // 4, lv.PART.INDICATOR)

    lv.timer_create(glow_timer_cb, 500, None)

    # -----------------------------
    # CO2 update
    # -----------------------------
    def set_co2_cb(t):
        # max 4 chars as you requested
        value = int(var.sensor_data.co2_scd41)
        txt = str(int(value))[:4]
        co2_label.set_text(txt)

        if value < 1000:
            color = lv.color_hex(0x55FF00)
        elif value < 1500:
            color = lv.color_hex(0x00D0FF)
        else:
            color = lv.color_hex(0x303BFF)

        ring.set_style_arc_color(color, lv.PART.INDICATOR)
        ppm_label.set_style_text_color(color, 0)

        ring_g1.set_style_arc_color(color, lv.PART.INDICATOR)
        ring_g2.set_style_arc_color(color, lv.PART.INDICATOR)
        #ring_g3.set_style_arc_color(color, lv.PART.INDICATOR)
        #ring_g4.set_style_arc_color(color, lv.PART.INDICATOR)

    lv.timer_create(set_co2_cb, 500, None)

    # Enable swipe on full screen
    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    var.screens.append(scr)
    var.screen_names.append("CO2")

    return scr
    

def create_dummy_screen():
    
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

    var.screens.append(scr)
    var.screen_names.append("Dummy")
    
    #lv.screen_load(scr)
    
    return scr


def create_sensor_table():
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
    table.set_size(SCREEN_W, 900)
    table.align(lv.ALIGN.TOP_LEFT, 0, 0)

    # ✅ Make sure table itself does NOT scroll -> removes 2nd scrollbar
    table.remove_flag(lv.obj.FLAG.SCROLLABLE)
    table.set_scrollbar_mode(lv.SCROLLBAR_MODE.OFF)

    # (Optional but helps: remove table internal padding so it sits tighter)
    table.set_style_pad_top(0, 0)
    table.set_style_pad_bottom(0, 0)
    table.set_style_pad_left(0, 0)
    table.set_style_pad_right(0, 0)

    # 3 columns and 18 rows
    table.set_column_count(3)
    table.set_row_count(19)

    table.set_column_width(0, 5)
    table.set_column_width(1, 110)
    table.set_column_width(2, 125)

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
    table.set_cell_value(15, 1, "Date")
    table.set_cell_value(16, 1, "Time")
    table.set_cell_value(17, 1, "AP enabled")
    table.set_cell_value(18, 1, "WiFi")

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
        table.set_cell_value(1, 2, "{:.1f}".format(var.sensor_data.temp_qmi8658c))
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

        timestamp = localtime_with_offset()
        date_str = f"{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d}"
        time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
        table.set_cell_value(15, 2, date_str)
        table.set_cell_value(16, 2, time_str)

        table.set_cell_value(17, 2, "{}".format(var.ap_enabled))
        if var.wifi_connected:
            table.set_cell_value(18, 2, var.wifi_ip)
        elif var.wifi_sleep:
            table.set_cell_value(18, 2, "Sleep: "+str(int(var.sleep_till_next_connection)))
        else:
            table.set_cell_value(18, 2, "False")

    lv.timer_create(table_update_cb, 500, None)

    # Swipe on screen (fine)
    scr.add_event_cb(swipe_event_cb, lv.EVENT.ALL, None)

    var.screens.append(scr)
    var.screen_names.append("Sensors")
    return scr



def _battery_symbol_from_pct(pct):
    # LVGL has several battery glyphs in the built-in font
    if pct <= 5:
        return lv.SYMBOL.BATTERY_EMPTY
    elif pct <= 25:
        return lv.SYMBOL.BATTERY_1
    elif pct <= 50:
        return lv.SYMBOL.BATTERY_2
    elif pct <= 75:
        return lv.SYMBOL.BATTERY_3
    else:
        return lv.SYMBOL.BATTERY_FULL


def create_battery_widget(parent, right_pad=6, top_pad=2):
    """
    Returns a dict of LVGL objects you can update:
      w['cont'], w['icon'], w['bolt'], w['pct_lbl']
    """

    w = {}

    # Container on the right
    cont = lv.cont(parent)
    #cont.set_fit(lv.FIT.NONE)
    #cont.set_layout(lv.LAYOUT.OFF)
    cont.set_height(parent.get_height())
    cont.set_width(78)  # tweak if you want it tighter/wider
    cont.align(parent, lv.ALIGN.IN_RIGHT_MID, -right_pad, 0)
    cont.set_fit2(lv.FIT.TIGHT, lv.FIT.TIGHT)     # container hugs its children
    cont.set_layout(lv.LAYOUT.ROW_MID)            # children placed left→right, vertically centered
    cont.set_style_local_pad_inner(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 3)

    # Make it visually "flat"
    cont.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    cont.set_style_local_border_width(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    cont.set_style_local_outline_width(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    cont.set_style_local_shadow_width(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)

    # Percent label (fixed width-ish so it doesn't “jump”)
    pct_lbl = lv.label(cont)
    pct_lbl.set_text("100%")
    #pct_lbl.align(cont, lv.ALIGN.IN_LEFT_MID, 4, 0)

    # Battery icon
    icon = lv.label(cont)
    icon.set_text(lv.SYMBOL.BATTERY_FULL)
    #icon.align(cont, lv.ALIGN.IN_LEFT_MID, 0, 0)

    # Charging bolt overlay (hidden by default)
    bolt = lv.label(cont)
    # If your font has it, this looks nicer than plain "⚡"
    bolt.set_text(lv.SYMBOL.CHARGE)
    bolt.set_style_local_text_opa(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    #bolt.align(icon, lv.ALIGN.CENTER, 0, 0)



    w["cont"] = cont
    w["icon"] = icon
    w["bolt"] = bolt
    w["pct_lbl"] = pct_lbl
    return w


def set_battery_widget(w, pct, charging=False):
    """
    pct: 0..100
    charging: True/False
    """
    if pct < 0: pct = 0
    if pct > 100: pct = 100

    w["icon"].set_text(_battery_symbol_from_pct(pct))

    # Fixed-width formatting to reduce visual jitter
    w["pct_lbl"].set_text("{:>3d}%".format(pct))

    # Show/hide bolt (keep its space by using opacity)
    w["bolt"].set_style_local_text_opa(
        lv.label.PART.MAIN,
        lv.STATE.DEFAULT,
        lv.OPA.COVER if charging else lv.OPA.TRANSP
    )


def create_status_bar(top_layer):
    #global btn_left, btn_right

    status = lv.cont(top_layer, None)
    status.set_fit(lv.FIT.NONE)
    status.set_layout(lv.LAYOUT.OFF)
    status.set_width(SCREEN_W)
    status.set_height(STATUS_BAR_H)
    status.align(None, lv.ALIGN.IN_TOP_MID, 0, 0)

    status.set_style_local_border_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    status.set_style_local_outline_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    status.set_style_local_shadow_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
    status.set_style_local_radius(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)

    #wifi_icon = lv.label(status, None)
    #wifi_icon.set_text(SYMBOL_WIFI)

    #sd_icon = lv.label(status, None)
    #sd_icon.set_text(SYMBOL_SD)

    screen_label = lv.label(status)
    screen_label.set_text("SYSTEM")
    screen_label.align(status, lv.ALIGN.CENTER, 0, 0)
    
    time_row = lv.cont(status)
    time_row.set_fit2(lv.FIT.TIGHT, lv.FIT.TIGHT)     # container hugs its children
    time_row.set_layout(lv.LAYOUT.ROW_MID)            # children placed left→right, vertically centered
    # remove spacing between hour : minute
    time_row.set_style_local_pad_inner(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    # remove any visual borders of the container
    time_row.set_style_local_bg_opa(lv.obj.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
    time_row.set_style_local_border_width(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    time_row.set_style_local_pad_all(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    time_row.set_style_local_pad_inner(lv.obj.PART.MAIN, lv.STATE.DEFAULT, 0)
    # put the whole group where you want
    time_row.align(status, lv.ALIGN.IN_LEFT_MID, 5, 0)   # change pos as needed

    hour_lbl  = lv.label(time_row)
    colon_lbl = lv.label(time_row)
    min_lbl   = lv.label(time_row)

    hour_lbl.set_text("12")
    colon_lbl.set_text(":")
    min_lbl.set_text("34")
      
    previous_minute = ""
    previous_label = ""
    sec = 0
    
    batt = create_battery_widget(status)
    
    set_battery_widget(batt, 69, charging=False)
    
    '''
    def remove_button_style(btn):
        btn.set_style_local_border_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
        btn.set_style_local_outline_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
        btn.set_style_local_shadow_width(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
        btn.set_style_local_radius(lv.btn.PART.MAIN, lv.STATE.DEFAULT, 0)
        #btn.set_style_local_bg_opa(lv.btn.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)

    # Left button
    var.btn_left = lv.btn(status)
    var.btn_left.set_size(40, STATUS_BAR_H)
    var.btn_left.align(status, lv.ALIGN.IN_LEFT_MID, 0, 0)
    var.btn_left.set_event_cb(nav_btn_event_cb)

    lbl_l = lv.label(var.btn_left)
    lbl_l.set_text(lv.SYMBOL.LEFT)
    lbl_l.align(var.btn_left, lv.ALIGN.CENTER, 0, 0)

    # Right button
    var.btn_right = lv.btn(status)
    var.btn_right.set_size(40, STATUS_BAR_H)
    var.btn_right.align(None, lv.ALIGN.IN_RIGHT_MID, 0, 0)
    var.btn_right.set_event_cb(nav_btn_event_cb)

    lbl_r = lv.label(var.btn_right)
    lbl_r.set_text(lv.SYMBOL.RIGHT)
    lbl_r.align(var.btn_right, lv.ALIGN.CENTER, 0, 0)
    
    # Remove outlines
    remove_button_style(var.btn_left)
    remove_button_style(var.btn_right)
    '''
    
    style_hidden = lv.style_t()
    style_hidden.init()
    style_hidden.set_text_opa(lv.STATE.DEFAULT, lv.OPA.TRANSP)

    style_visible = lv.style_t()
    style_visible.init()
    style_visible.set_text_opa(lv.STATE.DEFAULT, lv.OPA.COVER)
    
    def update_screen_label_cb(timer):
        nonlocal previous_label
            
        label = var.screen_names[var.current_idx]
        
        if label != previous_label:
            s = label
            screen_label.set_text(s)
            previous_label = label
            
        else:
            return
        
    def update_time_labels_cb(timer):
        nonlocal sec, previous_minute, batt
        # read actual time from your var
        rtc = var.system_data.time_rtc

        if rtc is not None and type(rtc) == tuple:
            hour = rtc[4]
            minute = rtc[5]
        else:
            hour = 12
            minute = 34
        
        sec += 1
        
        #set_hidden removes the label from ui rendering :(
        #colon_lbl.set_hidden(sec % 2 == 0)
        if sec % 2 == 0:
            # invisible but still takes space
            colon_lbl.set_style_local_text_opa(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.TRANSP)
        else:
            # visible
            colon_lbl.set_style_local_text_opa(lv.label.PART.MAIN, lv.STATE.DEFAULT, lv.OPA.COVER)
            
        set_battery_widget(batt, int(var.system_data.bat_percentage), var.system_data.charging)
            
        if minute != previous_minute:
            # format HH:MM with leading zeros
            #s = "{:02}  {:02}".format(hour, minute)
            s = "{:02}".format(hour)
            hour_lbl.set_text(s)

            s = "{:02}".format(minute)
            min_lbl.set_text(s)
            
            previous_minute = minute
            
        else:
            return
        
    # --- Update screen label in every 50ms ---
    lv.task_create(update_screen_label_cb, 50, lv.TASK_PRIO.LOW, None)
    # --- Update time labels in every 1000ms ---
    lv.task_create(update_time_labels_cb, 1000, lv.TASK_PRIO.LOW, None)