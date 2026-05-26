from lv_port import init
import time
import sys

if sys.platform == "darwin":
    SIMULATOR = True
else:
    SIMULATOR = False

# ---- Global variables ----
if SIMULATOR:
    import fake_shared_variables as var
else:
    import shared_variables as var

SCREEN_H = 240
SCREEN_W = 240

font_consolas_14 = None
font_montserrat_16_semibold = None
_font_fs_drv = None

def load_fonts():
    global font_consolas_14, font_montserrat_16_semibold, _font_fs_drv

    if font_consolas_14 is not None:
        return

    lv = init()

    # Load a custom font in bin format converted by https://lvgl.io/tools/fontconverter
    # Use this range during conversion to include special characters too:
    # 0x20-0x7F,0xA0-0x17F,0x2000-0x206F,0x20A0-0x20CF,0x2100-0x214F,0x2200-0x22FF,0x25A0-0x25FF
    import fs_driver
    _font_fs_drv = lv.fs_drv_t()
    fs_driver.fs_register(_font_fs_drv, 'S')
    font_consolas_14 = lv.binfont_create("S:fonts/font_consolas_14.bin")
    font_montserrat_16_semibold = lv.binfont_create("S:fonts/font_montserrat_16_semibold.bin")

def localtime_with_offset(offset_sec=var.TZ_OFFSET):
    # get current UTC epoch
    utc_epoch = time.time()
        
    # apply offset
    local_epoch = utc_epoch + offset_sec
    
    # convert back to tuple
    return time.localtime(local_epoch)

def is_screen_active(name, group="normal"):
    if group == "alt":
        return (
            var.selected_alt and
            not var.selected_game and
            len(var.screen_names_alt) > 0 and
            var.screen_names_alt[var.current_idx_alt] == name
        )

    if group == "game":
        return (
            var.selected_game and
            len(var.screen_names_game) > 0 and
            var.screen_names_game[var.current_idx_game] == name
        )

    return (
        not var.selected_alt and
        not var.selected_game and
        len(var.screen_names) > 0 and
        var.screen_names[var.current_idx] == name
    )

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
