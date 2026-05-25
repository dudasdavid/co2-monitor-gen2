from micropython import const  # NOQA
import lcd_bus  # NOQA
from lv_port import init
import time

lv = None
bus = None
display = None
mouse = None
th = None

def init_display():
  global lv, bus, display, mouse, th

  lv = init()

  _WIDTH = const(240)
  _HEIGHT = const(240)

  bus = lcd_bus.SDLBus(flags=0)

  buf1 = bus.allocate_framebuffer(_WIDTH * _HEIGHT * 3, 0)

  import sdl_display  # NOQA

  display = sdl_display.SDLDisplay(
      data_bus=bus,
      display_width=_WIDTH,
      display_height=_HEIGHT,
      frame_buffer1=buf1,
      color_space=lv.COLOR_FORMAT.RGB888,
  )
  display.init()

  import sdl_pointer
  import task_handler

  mouse = sdl_pointer.SDLPointer()

  # the duration needs to be set to 5 to have a good response from the mouse.
  # There is a thread that runs that facilitates double buffering. 
  th = task_handler.TaskHandler(duration=5)

def main():

  init_display()

  from ui import ui_generic
  from ui import ui_chart
  from ui import ui_games
  from ui import ui_sensors
  from ui import ui_settings
  from ui import ui_table
  from ui import ui_welcome

  scr1 = ui_table.create_sensor_table(alt = True)
  scr2 = ui_sensors.create_co2_screen()
  scr3 = ui_chart.create_co2_chart_screen()
  scr4 = ui_sensors.create_sensor_screen()
  scr5 = ui_settings.create_timezone_screen(alt = True)
  scr6 = ui_settings.create_ap_screen(alt = True)
  scr7 = ui_settings.create_roll_indicator_screen(alt = True)
  scr8 = ui_games.create_snake_screen(game = True)["scr"]
  scr9 = ui_welcome.create_welcome_screen()

  lv.screen_load(scr9)

  # If not running from REPL this keeps it alive.
  while True:
      time.sleep_ms(100)

if __name__ == "__main__" or __name__ == "simulator":
  main()
