from lv_port import init

# ---- Global variables ----
import shared_variables as var

def create_welcome_screen():
    
    lv = init()
    
    # use fs_driver in case of loading png from filesystem, but decoding is too slow
    #import fs_driver
    #fs_drv = lv.fs_drv_t()
    #fs_driver.fs_register(fs_drv, 'S')
    
    # Use an binary image converted by https://lvgl.io/tools/imageconverter
    with open("/images/welcome.bin", "rb") as f:
        welcome_buf = f.read()
        
    # Create an image header for the binary image
    welcome_img = lv.image_dsc_t({
        "header": {
            "cf": lv.COLOR_FORMAT.RGB565,
            "w": 240,
            "h": 240,
        },
        "data_size": len(welcome_buf),
        "data": welcome_buf,
    })
    
    # Create a new screen
    scr = lv.obj()
    scr.set_style_bg_color(lv.color_hex(0x000000), 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)
    scr.set_style_border_width(0, 0)

    # Welcome label with plain text
    #label = lv.label(scr)
    #label.set_text("Welcome")
    #label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
    #label.set_style_text_font(lv.font_montserrat_28, 0)
    #label.center()
    
    # Create image object
    img = lv.image(scr)
    # Load image from filesystem
    #img.set_src("S:/images/welcome.png")
    img.set_src(welcome_img)
    # Center image
    img.center()
    
    # Intentionally not adding the screen to available screens, so the user cannot switch back to it later
    #var.screens.append(scr)
    #var.screen_names.append("Welcome")

    # Load the screen
    lv.screen_load(scr)

    return scr