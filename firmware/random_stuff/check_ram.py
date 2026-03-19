import gc
gc.collect()
free = gc.mem_free()
used = gc.mem_alloc()
total = free + used

print("RAM total:", total/1024, "kB, free:", free/1024, "kB, used:", used/1024, "kB")
