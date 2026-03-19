# lv_port.py
import lvgl as lv

_lv_inited = False

def init():
    global _lv_inited
    if _lv_inited:
        return lv

    lv.init()

    # TODO: init your display + touch drivers ONCE here
    # display_init()
    # indev_init()

    _lv_inited = True
    return lv