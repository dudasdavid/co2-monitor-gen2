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

def create_snake_screen(alt=False, game=True):

    lv = init()

    scr = lv.obj()
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.remove_flag(lv.obj.FLAG.SCROLLABLE)

    ui.load_fonts()

    wall_color = lv.color_hex(0x00FF55)
    wall_dim_color = lv.color_hex(0x123A25)
    text_color = lv.color_hex(0xC8E8D2)
    head_color = lv.color_hex(0x00FF55)
    body_color = lv.color_hex(0x00B844)
    # The SDL/display color ordering renders this as warm amber.
    food_color = lv.color_hex(0x00A5FF)

    # Curved controls prompt on the outer rim
    title = lv.arclabel(scr)
    title.set_size(240, 240)
    title.center()
    title.set_text("<  TURN  >")
    title.set_style_text_font(ui.font_montserrat_16_semibold, 0)
    title.set_style_text_color(text_color, 0)
    title.set_radius(101)
    title.set_angle_start(225)
    title.set_angle_size(90)
    title.set_text_vertical_align(lv.arclabel.TEXT_ALIGN.CENTER)
    title.set_text_horizontal_align(lv.arclabel.TEXT_ALIGN.CENTER)

    # Edge-to-edge glowing arena wall frames the round display.
    ring_glow = lv.arc(scr)
    ring_glow.remove_style_all()
    ring_glow.remove_flag(lv.obj.FLAG.CLICKABLE)
    ring_glow.set_size(240, 240)
    ring_glow.align(lv.ALIGN.CENTER, 0, 0)
    ring_glow.set_rotation(270)
    ring_glow.set_bg_angles(0, 360)
    ring_glow.set_range(0, 100)
    ring_glow.set_value(100)
    ring_glow.set_style_pad_all(0, 0)
    ring_glow.set_style_arc_width(7, lv.PART.INDICATOR)
    ring_glow.set_style_arc_color(wall_color, lv.PART.INDICATOR)
    ring_glow.set_style_arc_opa(lv.OPA._20, lv.PART.INDICATOR)

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
    ring.set_style_arc_color(wall_dim_color, lv.PART.MAIN)
    ring.set_style_arc_opa(lv.OPA.COVER, lv.PART.MAIN)

    ring.set_style_arc_width(2, lv.PART.INDICATOR)
    ring.set_style_arc_color(wall_color, lv.PART.INDICATOR)
    ring.set_style_arc_opa(lv.OPA.COVER, lv.PART.INDICATOR)

    score_lbl = lv.arclabel(scr)
    score_lbl.set_size(240, 240)
    score_lbl.center()
    score_lbl.set_style_text_font(ui.font_montserrat_16_semibold, 0)
    score_lbl.set_style_text_color(text_color, 0)
    score_lbl.set_radius(101)
    score_lbl.set_angle_start(45)
    score_lbl.set_angle_size(90)
    score_lbl.set_dir(lv.arclabel.DIR.COUNTER_CLOCKWISE)
    score_lbl.set_text_vertical_align(lv.arclabel.TEXT_ALIGN.CENTER)
    score_lbl.set_text_horizontal_align(lv.arclabel.TEXT_ALIGN.CENTER)
    title.move_foreground()
    score_lbl.move_foreground()

    # Snake game logic
    GRID_W = 24
    GRID_H = 24
    CELL = 10
    ARENA_RADIUS = 112
    FOOD_RADIUS = 104

    snake = [(5, 12), (4, 12), (3, 12)]
    food = [15, 12]
    direction = [1, 0]
    score = 0
    feedback = {"food_ticks": 0, "turn_ticks": 0}

    cells = []

    game_w = GRID_W * CELL
    game_h = GRID_H * CELL
    offset_x = (240 - game_w) // 2
    offset_y = (240 - game_h) // 2

    def make_cell():
        o = lv.obj(scr)
        o.set_size(CELL - 1, CELL - 1)
        o.set_style_bg_opa(lv.OPA.COVER, 0)
        o.set_style_border_width(0, 0)
        o.remove_flag(lv.obj.FLAG.CLICKABLE)
        o.remove_flag(lv.obj.FLAG.SCROLLABLE)
        return o

    def make_food_marker(size, opa):
        o = lv.obj(scr)
        o.set_size(size, size)
        o.set_style_radius(size // 2, 0)
        o.set_style_bg_color(food_color, 0)
        o.set_style_bg_opa(opa, 0)
        o.set_style_border_width(0, 0)
        o.remove_flag(lv.obj.FLAG.CLICKABLE)
        o.remove_flag(lv.obj.FLAG.SCROLLABLE)
        return o

    food_halo = make_food_marker(17, lv.OPA._20)
    food_obj = make_food_marker(9, lv.OPA.COVER)

    def place_obj(o, x, y, size):
        o.set_pos(
            offset_x + x * CELL + (CELL - size) // 2,
            offset_y + y * CELL + (CELL - size) // 2
        )

    def update_score():
        score_lbl.set_text("SCORE %02d" % score)

    def update_feedback():
        if feedback["food_ticks"] > 0:
            ring.set_style_arc_color(food_color, lv.PART.INDICATOR)
            ring_glow.set_style_arc_opa(lv.OPA._60, lv.PART.INDICATOR)
            food_halo.set_style_bg_opa(lv.OPA._50, 0)
            feedback["food_ticks"] -= 1
        else:
            ring.set_style_arc_color(wall_color, lv.PART.INDICATOR)
            ring_glow.set_style_arc_opa(lv.OPA._20, lv.PART.INDICATOR)
            food_halo.set_style_bg_opa(lv.OPA._20, 0)

        if feedback["turn_ticks"] > 0:
            title.set_style_text_color(wall_color, 0)
            feedback["turn_ticks"] -= 1
        else:
            title.set_style_text_color(text_color, 0)

    def draw():
        nonlocal cells

        while len(cells) < len(snake):
            cells.append(make_cell())

        for i, (x, y) in enumerate(snake):
            size = CELL - 1
            radius = size // 2
            if i == 0:
                color = head_color
            else:
                color = body_color

            cells[i].set_size(size, size)
            cells[i].set_style_radius(radius, 0)
            cells[i].set_style_bg_color(color, 0)
            cells[i].set_style_shadow_width(6 if i == 0 else 0, 0)
            cells[i].set_style_shadow_color(head_color, 0)
            cells[i].set_style_shadow_opa(lv.OPA._50 if i == 0 else lv.OPA.TRANSP, 0)
            cells[i].remove_flag(lv.obj.FLAG.HIDDEN)
            place_obj(cells[i], x, y, size)

        for i in range(len(snake), len(cells)):
            cells[i].add_flag(lv.obj.FLAG.HIDDEN)

        place_obj(food_halo, food[0], food[1], 17)
        place_obj(food_obj, food[0], food[1], 9)

    def new_food():
        # Round display parameters
        cx = GRID_W * CELL // 2
        cy = GRID_H * CELL // 2
        # place foods within a smaller circle than the screen (and walls)
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
            if dx * dx + dy * dy <= FOOD_RADIUS * FOOD_RADIUS:
                return [gx, gy]

    def reset_game():
        nonlocal snake, food, direction, score
        snake = [(5, 12), (4, 12), (3, 12)]
        direction = [1, 0]
        score = 0
        feedback["food_ticks"] = 0
        food = new_food()
        update_score()
        draw()

    def snake_tick(timer):
        nonlocal snake, food, score

        if not ui.is_screen_active("Snake", "game") and not ui.SIMULATOR:
            return

        update_feedback()

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
        dxc = px - cx
        dyc = py - cy

        outside_circle = (
            dxc * dxc + dyc * dyc > ARENA_RADIUS * ARENA_RADIUS
        )

        if outside_circle or new_head in snake:
            reset_game()
            return

        snake.insert(0, new_head)

        if nx == food[0] and ny == food[1]:
            score += 1
            food = new_food()
            feedback["food_ticks"] = 2
            update_score()
            update_feedback()
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
        feedback["turn_ticks"] = 1
        update_feedback()

    def turn_right():
        dx = direction[0]
        dy = direction[1]

        # 90° CW
        direction[0] = dy
        direction[1] = -dx
        feedback["turn_ticks"] = 1
        update_feedback()

    def simulator_click_cb(e):
        indev = lv.indev_active()
        if indev is None:
            return

        point = lv.point_t()
        indev.get_point(point)
        if point.y < ui.SCREEN_H // 2:
            turn_right()
        else:
            turn_left()

    update_score()
    draw()

    snake_timer = lv.timer_create(snake_tick, 400, None)

    if ui.SIMULATOR:
        scr.add_flag(lv.obj.FLAG.CLICKABLE)
        scr.add_event_cb(simulator_click_cb, lv.EVENT.CLICKED, None)

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
