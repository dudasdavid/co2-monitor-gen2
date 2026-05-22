from lv_port import init
from math import ceil, sin
import time
import random
import math

# --- Generic UI features --
from ui import ui_generic as ui

# ---- Global variables ----
import shared_variables as var

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
    page.set_size(ui.SCREEN_W, ui.SCREEN_H)
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
    table.set_size(ui.SCREEN_W, 24*30+100)
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
    table.set_cell_value(19, 1, "AP status")
    table.set_cell_value(20, 1, "WiFi status")
    table.set_cell_value(21, 1, "MQTT server")
    table.set_cell_value(22, 1, "/ storage")
    table.set_cell_value(23, 1, "RAM")
    
    # Default font type
    #table.set_style_text_font(lv.font_montserrat_14, 0)
    
    # Load a custom font in bin format converted by https://lvgl.io/tools/fontconverter
    # Use this range during conversion to include special characters too:
    # 0x20-0x7F,0xA0-0x17F,0x2000-0x206F,0x20A0-0x20CF,0x2100-0x214F,0x2200-0x22FF,0x25A0-0x25FF
    import fs_driver
    fs_drv = lv.fs_drv_t()
    fs_driver.fs_register(fs_drv, 'S')
    custom_font = lv.binfont_create("S:/fonts/font_consolas_14.bin")
    table.set_style_text_font(custom_font, 0) 

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

    cell_cache = {}

    def set_cell_if_changed(row, col, value):
        key = (row, col)
        if cell_cache.get(key) == value:
            return

        cell_cache[key] = value
        table.set_cell_value(row, col, value)

    def table_update_cb(task):
        if not ui.is_screen_active("Sensor table", "alt"):
            return

        set_cell_if_changed(0, 2, "{:.1f}".format(var.sensor_data.temp_scd41))
        if var.hw_variant == "i80":
            set_cell_if_changed(1, 2, "{:.1f}".format(var.sensor_data.temp_qmi8658c))
        elif var.hw_variant == "spi":
            set_cell_if_changed(1, 2, "{:.1f}".format(var.sensor_data.temp_ds3231))
        set_cell_if_changed(2, 2, "{:.1f}".format(var.sensor_data.humidity_scd41))
        set_cell_if_changed(3, 2, "{}".format(int(var.sensor_data.co2_scd41)))
        set_cell_if_changed(4, 2, "{:.2f}".format(var.sensor_data.lux_veml7700))
        set_cell_if_changed(5, 2, "{:.2f}".format(var.sensor_data.acc_qmi8658c[0]))
        set_cell_if_changed(6, 2, "{:.2f}".format(var.sensor_data.acc_qmi8658c[1]))
        set_cell_if_changed(7, 2, "{:.2f}".format(var.sensor_data.acc_qmi8658c[2]))
        set_cell_if_changed(8, 2, "{:.2f}".format(var.sensor_data.gyro_qmi8658c[0]))
        set_cell_if_changed(9, 2, "{:.2f}".format(var.sensor_data.gyro_qmi8658c[1]))
        set_cell_if_changed(10, 2, "{:.2f}".format(var.sensor_data.gyro_qmi8658c[2]))
        set_cell_if_changed(11, 2, "{:.2f}".format(var.system_data.bat_volt))
        set_cell_if_changed(12, 2, "{:.1f}".format(var.system_data.bat_percentage))
        set_cell_if_changed(13, 2, "{}".format(var.system_data.usb_connected))
        set_cell_if_changed(14, 2, "{}".format(var.system_data.buttons))

        timestamp = var.system_data.time_rtc
        date_str = f"{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d}"
        time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
        set_cell_if_changed(15, 2, date_str)
        set_cell_if_changed(16, 2, time_str)


        timestamp = ui.localtime_with_offset(var.TZ_OFFSET)
        date_str = f"{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d}"
        time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
        set_cell_if_changed(17, 2, date_str)
        set_cell_if_changed(18, 2, time_str)

        if var.ap_enabled:
            set_cell_if_changed(19, 2, "On: {}s".format(int(var.ap_disable_timer)))
        elif var.ap_request:
            set_cell_if_changed(19, 2, "Requested...")
        else:
            set_cell_if_changed(19, 2, "Disabled")
            
        if var.wifi_connected:
            set_cell_if_changed(20, 2, var.wifi_ip)
        elif var.ap_enabled:
            set_cell_if_changed(20, 2, "Disabled")
        elif var.wifi_connecting:
            set_cell_if_changed(20, 2, "Connecting...")
        elif var.wifi_sleep:
            set_cell_if_changed(20, 2, "Sleep: "+str(int(var.sleep_till_next_connection)))
        else:
            set_cell_if_changed(20, 2, "Disabled")

        set_cell_if_changed(21, 2, var.system_data.mqtt_server_connection)

        set_cell_if_changed(22, 2, "{:.1f} / {}MB".format(var.system_data.used_space_flash/1024.0, int(var.system_data.total_space_flash/1024)))
        set_cell_if_changed(23, 2, "{:.1f} / {}MB".format(var.system_data.used_heap/1024.0, int(var.system_data.total_heap/1024)))

    lv.timer_create(table_update_cb, 1000, None)

    # Swipe on screen (fine)
    scr.add_event_cb(ui.swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "Sensor table"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)
    return scr
