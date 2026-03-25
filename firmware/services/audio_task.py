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

CHUNK = 4096

def vol_db(db):
    # db: -60 … 0
    return 10 ** (db / 20)

VOLUME = vol_db(-12)   # sounds “half as loud”

def apply_volume(buf, volume):
    # volume: 0.0 … 1.0
    for i in range(0, len(buf), 2):
        s = struct.unpack_from('<h', buf, i)[0]
        s = int(s * volume)

        # clamp
        if s > 32767:
            s = 32767
        elif s < -32768:
            s = -32768

        struct.pack_into('<h', buf, i, s)

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

async def play_pcm(ch, rate, pcm, tail = 1):
    # i2s cannot be globally initialized and kept initialized because it crashes lvgl ui
    audio = I2S(
        0,
        sck=Pin(I2S_SCK_PIN),
        ws=Pin(I2S_WS_PIN),
        sd=Pin(I2S_SD_PIN),
        mode=I2S.TX,
        bits=16,
        format=I2S.MONO if ch == 1 else I2S.STEREO,
        rate=rate,
        ibuf=40000
    )
    
    try:
        mv = memoryview(pcm)
        for i in range(0, len(pcm), CHUNK):
            audio.write(mv[i:i+CHUNK])
            #await asyncio.sleep_ms(0)
        # push a little silence to flush the pipeline
        tail = bytearray(1024*tail) # 0s = silence (16-bit PCM)
        audio.write(tail)
    finally:
        audio.deinit()

async def audio_task():
    #Init
    log = Logger("wav", debug_enabled=True)
    # Load and play boot sound ASAP
    boot_ch, boot_rate, boot_pcm = load_wav_pcm("/sounds/oxp.wav")
    await play_pcm(boot_ch, boot_rate, boot_pcm, tail = 20)

    # Pre-load other sound samples to RAM
    click_ch, click_rate, click_pcm = load_wav_pcm("/sounds/click.wav")
    long_ch, long_rate, long_pcm = load_wav_pcm("/sounds/long_click.wav")

    #Run
    while True:
        event_type = await var.audio_events.get()
        log.debug("Audio event arrived:", event_type)
        if event_type == var.EVENT_AUDIO_SHORT:
            # A small sleep is needed for screen change otherwise lvgl will glitch due to i2s dma
            await asyncio.sleep_ms(80)
            await play_pcm(click_ch, click_rate, click_pcm, tail=35)
        elif event_type == var.EVENT_AUDIO_LONG:
            pass
            await play_pcm(long_ch, long_rate, long_pcm)
        else:
            pass
            await play_pcm(click_ch, click_rate, click_pcm)
