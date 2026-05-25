from lv_port import init
from math import ceil, sin
import time
import random
import math

# --- Generic UI features --
from ui import ui_generic as ui

# ---- Global variables ----
if ui.SIMULATOR:
    import fake_shared_variables as var
else:
    import shared_variables as var

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
    bat = ui.create_battery_widget(scr, 0, 111, font = lv.font_montserrat_16)

    # -----------------------------
    # Refresh callback
    # -----------------------------
    def refresh_cb(timer):
        if not ui.is_screen_active("Sensors") and not ui.SIMULATOR:
            return

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
    scr.add_event_cb(ui.swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Sensors"
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
    bat = ui.create_battery_widget(scr, 0, 87, font = lv.font_montserrat_16)
    
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
        if not ui.is_screen_active("CO2") and not ui.SIMULATOR:
            return

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
    scr.add_event_cb(ui.swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "CO2"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr
