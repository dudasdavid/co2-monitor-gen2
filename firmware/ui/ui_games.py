from lv_port import init
from math import ceil, sin
import time
import random
import math

# --- Generic UI features --
from ui import ui_generic as ui

# ---- Global variables ----
import shared_variables as var

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

    scr.add_event_cb(ui.swipe_event_cb, lv.EVENT.ALL, None)

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