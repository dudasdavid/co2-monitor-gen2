from machine import Pin, reset

p = Pin(0, Pin.OUT)
p.value(0)
reset()