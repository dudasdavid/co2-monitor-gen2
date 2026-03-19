from machine import I2S, Pin
import struct
import time

# --- pick GPIOs that are free on your ESP32-S3 board ---
SCK_PIN = 5   # BCLK
WS_PIN  = 4   # LRC
SD_PIN  = 7   # DIN

def vol_db(db):
    # db: -60 … 0
    return 10 ** (db / 20)

VOLUME = vol_db(-12)   # sounds “half as loud”
       
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

def play_wav(path, i2s_id=0, ibuf=20000):
    with open(path, "rb") as f:
        ch, rate, bits, data_size = _wav_info_and_seek_data(f)
        print("WAV:", ch, "ch,", rate, "Hz,", bits, "bit,", data_size, "bytes")
        bytes_per_sec = rate * ch * (bits // 8)
        print("Expected length:", data_size / bytes_per_sec, "sec")

        if bits != 16:
            raise ValueError("Use 16-bit PCM WAV for this player")
        if ch not in (1, 2):
            raise ValueError("Only mono/stereo supported")

        audio = I2S(
            i2s_id,
            sck=Pin(SCK_PIN),
            ws=Pin(WS_PIN),
            sd=Pin(SD_PIN),
            mode=I2S.TX,
            bits=16,
            format=I2S.MONO if ch == 1 else I2S.STEREO,
            rate=rate,
            ibuf=ibuf
        )


        buf = bytearray(4096)
        mv = memoryview(buf)

        remaining = data_size
        while remaining > 0:
            n = f.readinto(mv)
            if n <= 0:
                break
            
            #apply_volume(mv[:n], VOLUME)
            audio.write(mv[:n])   # blocking write
            remaining -= n

        # 1) push a little silence to flush the pipeline
        tail = bytearray(2048)          # 0s = silence (16-bit PCM)
        audio.write(tail)

        # 2) give the DAC time to actually play what's buffered
        time.sleep_ms(500)               # 40–150ms works well in practice

        audio.deinit()

# Example:
play_wav("/voice.wav", i2s_id=0)