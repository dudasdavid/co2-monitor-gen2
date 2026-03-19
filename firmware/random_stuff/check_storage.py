import os
import time
 
# Get file system stats
stats = os.statvfs('/flash')

block_size = stats[0]
total_blocks = stats[2]
free_blocks = stats[3]

total_space = block_size * total_blocks
free_space = block_size * free_blocks
used_space = total_space - free_space

print("Total space:", total_space / 1024, "kB")
print("Used space:", used_space / 1024, "kB")
print("Free space:", free_space / 1024, "kB")

def is_sd_mounted(path="/sd1"):
    try:
        os.statvfs(path)
        return True
    except OSError:
        return False
    
# Mount SD card
if not is_sd_mounted("/sd1"):
    import pyb
    sd = pyb.SDCard()
    sd.info()

    try:
        print("Try mounting SD card")
        os.mount(sd, '/sd1')
    except Exception as e:
        print("Failed to mount SD card:", e)
        print("Recovery with SD card power off")
        sd.power(False)
        time.sleep(1)
        sd.power(True)
        time.sleep(1)
        os.mount(sd, '/sd1')
else:
    print("SD card already mounted")



# Get file system stats
stats = os.statvfs('/sd1')

block_size = stats[0]
total_blocks = stats[2]
free_blocks = stats[3]

total_space = block_size * total_blocks
free_space = block_size * free_blocks
used_space = total_space - free_space

print("Total space:", total_space / 1024, "kB")
print("Used space:", used_space / 1024, "kB")
print("Free space:", free_space / 1024, "kB")



print(os.uname())

'''
import uos

for path in ('/', '/flash', '/sd'):
    try:
        print(path, uos.statvfs(path))
    except OSError as e:
        print(path, '-> OSError:', e)
'''


'''
SD card recovery logic:
1) Unmount: os.umount("/sd")
2) Turn off power: sd.power(False)
3) Turn on power: sd.power(True)
4) Mount it again: os.mount(sd, "/sd")

Issue: if SD card removed (or put back later) and not unmounted filesystem still looks like working,
os.listdir("/sd") returns the folder.
Although looking into subfolders doesn't work and also reading/writing files.

We need a logic to roboustly check that SD card is present and it really works.

os.statvfs('/sd') also gives true-like results when SD is already removed
sd.info() too
sd.present() might be useful

'''

