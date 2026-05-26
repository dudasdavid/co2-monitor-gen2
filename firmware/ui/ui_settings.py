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
        if not ui.is_screen_active("Roll", "alt") and not ui.SIMULATOR:
            return

        update_screen()

    lv.timer_create(timer_cb, 100, None)

    # Swipe gestures
    scr.add_event_cb(ui.swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Roll"

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
    btn_ap.set_style_bg_color(lv.color_hex(0x007D99), lv.STATE.PRESSED)
    btn_ap.set_style_border_width(2, lv.STATE.PRESSED)
    btn_ap.set_style_border_color(lv.color_hex(0xA8F0FF), lv.STATE.PRESSED)
    btn_ap.set_style_translate_y(2, lv.STATE.PRESSED)

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
        if not ui.is_screen_active("Access Point", "alt") and not ui.SIMULATOR:
            return

        try:
            update_button_state()
        except Exception as e:
            print("AP timer error:", e)

    ap_timer = lv.timer_create(ap_timer_cb, 2000, None)

    # Initial state
    update_button_state()

    # Swipe support
    scr.add_event_cb(ui.swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Access Point"
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
        #var.audio_events.put_nowait(var.EVENT_AUDIO_SHORT)
        
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
            if ui.SIMULATOR:
                raise Exception("No file writing in simulator")

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

    def style_adjust_button(btn):
        btn.set_style_bg_color(lv.color_hex(0x333333), 0)
        btn.set_style_bg_color(lv.color_hex(0x007D99), lv.STATE.PRESSED)
        btn.set_style_radius(10, 0)
        btn.set_style_border_width(0, 0)
        btn.set_style_border_width(2, lv.STATE.PRESSED)
        btn.set_style_border_color(lv.color_hex(0xA8F0FF), lv.STATE.PRESSED)
        btn.set_style_translate_y(2, lv.STATE.PRESSED)

    # Keep the short title gently curved and visually centered along the top rim.
    title = lv.arclabel(scr)
    title.set_size(240, 240)
    title.center()
    title.set_text("TIME ZONE")
    ui.load_fonts()
    title.set_style_text_font(ui.font_montserrat_16_semibold, 0)
    title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    title.set_radius(102)
    title.set_angle_start(225)
    title.set_angle_size(90)
    title.set_text_horizontal_align(lv.arclabel.TEXT_ALIGN.CENTER)

    # Center label
    label = lv.label(scr)
    label.set_style_text_font(lv.font_montserrat_34, 0)
    label.align(lv.ALIGN.TOP_MID, 0, 110)

    # + BUTTON (top)
    btn_plus = lv.obj(scr)
    btn_plus.set_size(100, 60)
    btn_plus.align(lv.ALIGN.TOP_MID, 0, 40)

    style_adjust_button(btn_plus)

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

    style_adjust_button(btn_minus)

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
    scr.add_event_cb(ui.swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Timezone"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr
