import uasyncio as asyncio
from machine import Pin, I2S
import gc
from logger import Logger
import time
import struct

# ---- Global variables ----
import shared_variables as var

I2S_SCK_PIN = const(5) # BCLK
I2S_WS_PIN  = const(4) # LRC
I2S_SD_PIN  = const(7) # Master DOUT / Slave DIN

CHUNK = 1024

def _wav_info_and_seek_data(f):
    # Minimal WAV parser (PCM only)
    if f.read(4) != b'RIFF':
        raise ValueError("Not RIFF")
    f.read(4)  # size
    if f.read(4) != b'WAVE':
        raise ValueError("Not WAVE")

    num_channels = None
    sample_rate = None
    bits = None

    # scan chunks
    while True:
        hdr = f.read(8)
        if len(hdr) < 8:
            raise ValueError("WAV: missing data chunk")
        cid = hdr[0:4]
        csz = struct.unpack("<I", hdr[4:8])[0]

        if cid == b'fmt ':
            fmt = f.read(csz)
            audio_format = struct.unpack("<H", fmt[0:2])[0]
            if audio_format != 1:
                raise ValueError("WAV not PCM")
            num_channels = struct.unpack("<H", fmt[2:4])[0]
            sample_rate = struct.unpack("<I", fmt[4:8])[0]
            bits = struct.unpack("<H", fmt[14:16])[0]

        elif cid == b'data':
            # file pointer now at PCM data start
            return num_channels, sample_rate, bits, csz
        else:
            f.seek(csz, 1)

def load_wav_pcm(path):
    with open(path, "rb") as f:
        ch, rate, bits, data_size = _wav_info_and_seek_data(f)
        if bits != 16:
            raise ValueError("Only 16-bit PCM")
        data = f.read(data_size)
        return ch, rate, data

async def play_pcm(pcm, tail = 0):
    # cannot initialize i2s globally, due to several glitches with DMA pressure
    audio = I2S(
        0,
        sck=Pin(I2S_SCK_PIN),
        ws=Pin(I2S_WS_PIN),
        sd=Pin(I2S_SD_PIN),
        mode=I2S.TX,
        bits=16,         # All samples are 16-bit PCM
        format=I2S.MONO, # All samples are MONO
        rate=8000,       # All samples are 8kHz
        ibuf=3000
    )
    
    sw = asyncio.StreamWriter(audio)
    
    try:
        mv = memoryview(pcm)

        for i in range(0, len(pcm), CHUNK):
            sw.write(mv[i:i + CHUNK])
            await sw.drain()          # non-blocking feed to I2S

        if tail > 0:
            tail = bytearray(1024 * tail)
            sw.write(tail)
            await sw.drain()

        # Give the hardware a short moment to finish shifting out the last DMA-buffered samples.
        await asyncio.sleep_ms(20)

    finally:
        audio.deinit()

async def audio_task():
    #Init
    log = Logger("i2s", debug_enabled=True)
    
    # Load and play boot sound ASAP
    boot_ch, boot_rate, boot_pcm = load_wav_pcm("/sounds/oxp.wav")
    await play_pcm(boot_pcm, tail = 1)

    # Pre-load other sound samples to RAM
    click_ch, click_rate, click_pcm = load_wav_pcm("/sounds/click.wav")
    long_ch, long_rate, long_pcm = load_wav_pcm("/sounds/long_click.wav")
    off_ch, off_rate, off_pcm = load_wav_pcm("/sounds/winxpshutdown.wav")

    #Run
    while True:
        event_type = await var.audio_events.get()
        log.debug("Audio event arrived:", event_type)
        if event_type == var.EVENT_AUDIO_SHORT:
            # A small sleep is needed for screen change otherwise i80 display driver will glitch due to i2s dma
            if var.hw_variant == "i80":
                await asyncio.sleep_ms(20)
            elif var.hw_variant == "spi":
                await asyncio.sleep_ms(20)
            await play_pcm(click_pcm)
        elif event_type == var.EVENT_AUDIO_LONG:
            pass
            await play_pcm(long_pcm)
        elif event_type == var.EVENT_AUDIO_OFF:
            await asyncio.sleep_ms(100)
            await play_pcm(off_pcm)
        else:
            pass
            await play_pcm(click_pcm)
