from machine import SPI, SDCard
import vfs, os


spi_bus = SPI.Bus(
    host=1,
    miso=48, 
    mosi=47,
    sck=41
)


sd = SDCard(
    spi_bus=spi_bus,
    cs=40,
    freq=1000000
)

#os.VfsFat.mkfs(sd)

vfs.mount(sd, "/sd1")
print('Flash Mounted')
print(os.listdir('/sd1'))

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
