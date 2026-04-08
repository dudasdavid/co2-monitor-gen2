import uasyncio as asyncio
import time
import network
import socket
import ntptime
#from my_wifi import SSID, PASSWORD
import sys
import gc
import machine

def load_wifi_creds():
    # Reload my_wifi so changes in file take effect without reboot
    if "my_wifi" in sys.modules:
        del sys.modules["my_wifi"]
    import my_wifi
    return my_wifi.SSID, my_wifi.PASSWORD

def save_wifi_creds(ssid, password):
    # Write valid Python with proper escaping using %r
    with open("my_wifi.py", "w") as f:
        f.write('SSID=%r\n' % ssid)
        f.write('PASSWORD=%r\n' % password)

from logger import Logger

# ---- Global variables ----
import shared_variables as var

log = Logger("network", debug_enabled=True)

def _now_ms():
    # Prefer monotonic ticks on MicroPython
    try:
        return time.ticks_ms()
    except AttributeError:
        # Fallback (lower resolution, not wrap-safe)
        return int(time.time() * 1000)

def _ms_since(t0_ms, t1_ms):
    # Wrap-safe if ticks_ms exists
    try:
        return time.ticks_diff(t1_ms, t0_ms)
    except AttributeError:
        return t1_ms - t0_ms

def _url_decode(s):
    # minimal x-www-form-urlencoded decode
    s = s.replace("+", " ")
    out = ""
    i = 0
    while i < len(s):
        if s[i] == "%" and i + 2 < len(s):
            try:
                out += chr(int(s[i+1:i+3], 16))
                i += 3
                continue
            except:
                pass
        out += s[i]
        i += 1
    return out

def _parse_form(body):
    # returns dict
    res = {}
    for part in body.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            res[_url_decode(k)] = _url_decode(v)
    return res

async def _read_http_request(reader):
    # Read request line
    line = await reader.readline()
    if not line:
        return None
    try:
        line = line.decode().strip()
    except:
        return None

    parts = line.split()
    if len(parts) < 2:
        return None
    method = parts[0]
    path = parts[1]

    # Read headers
    headers = {}
    while True:
        h = await reader.readline()
        if not h:
            break
        if h == b"\r\n":
            break
        try:
            hs = h.decode().strip()
        except:
            continue
        if ":" in hs:
            k, v = hs.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    body = b""
    if method == "POST":
        cl = headers.get("content-length", None)
        if cl is not None:
            try:
                n = int(cl)
                if n > 0:
                    body = await reader.readexactly(n)
            except:
                body = b""

    return method, path, headers, body

def _page_html(current_ssid="", msg=""):
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Pico WiFi Setup</title>
  <style>
    body{font-family:system-ui,Arial;margin:24px;max-width:520px}
    input{width:100%%;padding:10px;font-size:16px;margin:8px 0}
    button{padding:10px 14px;font-size:16px}
    .msg{margin:10px 0;color:#0a0}
    .err{margin:10px 0;color:#a00}
    .card{padding:16px;border:1px solid #ddd;border-radius:12px}
  </style>
</head>
<body>
  <h2>CO2 Monitor WiFi Setup</h2>
  <div class="card">
    %s
    <form method="POST" action="/save">
      <label>SSID</label>
      <input name="ssid" placeholder="WiFi name" value="%s" required>
      <label>Password</label>
      <input name="password" type="password" placeholder="WiFi password">
      <button type="submit">Save &amp; Connect</button>
    </form>
  </div>
</body>
</html>
""" % (msg, current_ssid)

async def wifi_setup_http_server(log):
    # Simple AP portal on port 80, exits when var.ap_request becomes False
    # Assumes AP is already active.
    try:
        ssid0, _ = load_wifi_creds()
    except:
        ssid0 = ""

    async def handler(reader, writer):
        try:
            req = await _read_http_request(reader)
            if not req:
                await writer.aclose()
                return

            method, path, headers, body = req

            if method == "GET" and (path == "/" or path.startswith("/?")):
                html = _page_html(current_ssid=ssid0, msg="")
                await writer.awrite("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
                await writer.awrite(html)
                await writer.aclose()
                return

            if path.startswith("/save") and method == "POST":
                try:
                    form = _parse_form(body.decode())
                except:
                    form = {}

                new_ssid = form.get("ssid", "").strip()
                new_pw = form.get("password", "")

                if not new_ssid:
                    html = _page_html(current_ssid="", msg='<div class="err">SSID is required.</div>')
                    await writer.awrite("HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
                    await writer.awrite(html)
                    await writer.aclose()
                    return

                # Save creds
                try:
                    save_wifi_creds(new_ssid, new_pw)
                    log.info("Saved new WiFi credentials to my_wifi.py")
                    var.ssid_save_successful = True
                except Exception as e:
                    log.error("Failed to save WiFi creds:", e)
                    html = _page_html(current_ssid=new_ssid, msg='<div class="err">Save failed.</div>')
                    await writer.awrite("HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
                    await writer.awrite(html)
                    await writer.aclose()
                    return

                # Tell your main task to exit AP mode
                var.ap_request = False

                # Redirect to / (optional)
                await writer.awrite("HTTP/1.1 303 See Other\r\nLocation: /\r\nConnection: close\r\n\r\n")
                await writer.aclose()
                writer.close()
                return

            # 404
            await writer.awrite("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
            await writer.aclose()

        except Exception as e:
            try:
                log.error("HTTP handler error:", e)
                await writer.aclose()
            except:
                pass

    server = await asyncio.start_server(handler, "0.0.0.0", 80)
    log.info("WiFi setup portal running on http://192.168.4.1/ (typical)")

    # Keep server alive while ap_request is True
    try:
        while var.ap_request:
            await asyncio.sleep_ms(200)
    finally:
        server.close()
        try:
            await server.wait_closed()
        except:
            pass
        log.info("WiFi setup portal stopped")
        #if var.ssid_save_successful:
            #log.warning("New WiFi credentials were saved, restart....")
            #machine.reset()
            

async def wifi_connect(wlan, timeout_s = 30):
    SSID, PASSWORD = load_wifi_creds()
    

    # ---- CONNECT TO WIFI ----
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    start_ms = _now_ms()
    timeout_ms = timeout_s * 1000
    log.info("Connecting to WiFi SSID:", SSID)
    var.wifi_connecting = True
    while not wlan.isconnected():
        
        # If user requests AP mode while trying to connect, abort quickly
        if var.ap_request:
            log.info("AP requested during STA connect -> abort connect")
            wlan.disconnect()
            wlan.active(False)
            var.wifi_connected = False
            return False
        
        if _ms_since(start_ms, _now_ms()) > timeout_ms:
            print(".") # Print a final dot to start a new line
            log.error("WiFi connection timed out!")
            wlan.disconnect()
            wlan.active(False)
            var.wifi_connected = False
            var.wifi_connecting = False
            return False
        
        print(".", end="")
        await asyncio.sleep_ms(500)

    print(".") # Print a final dot to start a new line
    log.info("WiFi connected! IP address:", wlan.ifconfig()[0])
    var.wifi_ip = wlan.ifconfig()[0]
    var.wifi_connecting = False

    # ---- SYNC TIME FROM NTP ----
    log.info("Fetching time from NTP...")
    try:
        ntptime.settime()  # sets internal RTC to UTC
        log.info("Time synchronized.")
        var.ntp_time_synchronized = True        
    
    except Exception as e:
        log.error("NTP sync failed:", e)
        var.ntp_time_synchronized = False
    
    var.wifi_connected = True
    return True

def wifi_disconnect(wlan):
    try:
        log.info("Disconnecting from WiFi...")
        wlan.disconnect()
        wlan.active(False)
        var.wifi_connected = False
        return True
    except Exception as e:
        log.error("WiFi disconnection failed:", e)
        wlan.active(False)
        var.wifi_connected = False
        return False

def ap_start(ap):
    log.info("Enabling access point...")
    ap.active(True)
    # Optional but recommended: set AP name + password
    # (authmode constants vary by port; on Pico W this is usually OK)
    try:
        ap.config(essid="CO2Monitor-Setup", password="12345678")
        # If your port supports authmode:
        # ap.config(authmode=network.AUTH_WPA_WPA2_PSK)
    except Exception as e:
        log.error("AP config failed (continuing):", e)

    var.ap_enabled = True

def ap_stop(ap):
    log.info("Disabling access point...")
    await asyncio.sleep_ms(100)
    gc.collect()
    
    try:
        ap.active(False)
    except Exception as e:
        log.error("AP stop error:", e)
        
    # Give time after stop too
    await asyncio.sleep_ms(200)
    gc.collect()
    var.ap_enabled = False


async def networking_task(period_on = 10.0, period_off = 50.0):
    #Init
    network.hostname("CO2-Sensor-SNr"+str(var.serial_number))
    ap = network.WLAN(network.AP_IF)
    wlan = network.WLAN(network.STA_IF)
    
    ap.active(False)
    wlan.active(False)

    #Run
    while True:
        
        var.wifi_ready_evt.clear()
        
        # --- AP MODE (setup portal) ---
        if var.ap_request:
            # ensure STA is off while in setup mode (simpler + more reliable)
            if wlan.active():
                wifi_disconnect(wlan)

            ap_start(ap)
            await wifi_setup_http_server(log)  # returns when var.ap_request becomes False
            await ap_stop(ap)

            # After AP mode exits, immediately attempt STA connect once
            log.info("Leaving AP setup mode, trying STA connect with new creds...")
            ok = await wifi_connect(wlan)
            log.info("Connected:", ok)
            if ok:
                var.wifi_ready_evt.set()

            # keep it on for period_on unless AP requested again
            t0 = _now_ms()
            while _ms_since(t0, _now_ms()) < int(period_on * 1000):
                if var.ap_request:
                    break
                await asyncio.sleep_ms(200)

            continue  # go back to top of loop (handles disconnect/off timing there)
        
        # --- NORMAL STA DUTY-CYCLE MODE ---
        log.info("Initiating WiFi connection...")
        connection_success = await wifi_connect(wlan)
        log.info("Connected:", connection_success)
        
        if connection_success:
            var.wifi_ready_evt.set()
            var.wifi_sleep = False
        
        # Stay on (but be interruptible by AP request)
        #await asyncio.sleep(period_on)
        t0 = _now_ms()
        await asyncio.sleep_ms(500)
        var.wifi_ready_evt.clear()
        
        
        while _ms_since(t0, _now_ms()) < int(period_on * 1000):
            if var.ap_request:
                break
            await asyncio.sleep_ms(200)
        
        
        
        if var.wifi_connected:
            log.info("Disconnecting WiFi connection...")
            disconnection_success = wifi_disconnect(wlan)
            log.info("Disconnected:", disconnection_success)
            var.wifi_sleep = True
        else:
            log.debug("WiFi is not connected, disconnection not needed.")
            
        # Off period (interruptible by AP request)
        t1 = _now_ms()
        while _ms_since(t1, _now_ms()) < int(period_off * 1000):
            var.sleep_till_next_connection = (period_off * 1000 - _ms_since(t1, _now_ms())) / 1000.0
            if var.ap_request:
                break
            await asyncio.sleep_ms(200)
            
        
if __name__ == "__main__":
    print("TESTING SINGLE TASK!")
    asyncio.run(networking_task(10, 30))
