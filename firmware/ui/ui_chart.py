from lv_port import init
from math import ceil, sin
import time
import random
import math

# --- Generic UI features --
from ui import ui_generic as ui

# ---- Global variables ----
import shared_variables as var

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
        if not ui.is_screen_active("CO2 chart"):
            return
        
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

    scr.add_event_cb(ui.swipe_event_cb, lv.EVENT.ALL, None)

    screen_name = "CO2 chart"
    if not alt:
        var.screens.append(scr)
        var.screen_names.append(screen_name)
    else:
        var.screens_alt.append(scr)
        var.screen_names_alt.append(screen_name)

    return scr
