from umqtt.simple import MQTTClient
import uasyncio as asyncio
import umqtt.config
import time
import json

from logger import Logger

# ---- Global variables ----
import shared_variables as var

log = Logger("mqtt", debug_enabled=True)

# MQTT Parameters for LAN connection
MQTT_SERVER_LOCAL = umqtt.config.mqtt_server_local
MQTT_PORT_LOCAL = umqtt.config.mqtt_port_local
MQTT_USER_LOCAL = umqtt.config.mqtt_username_local
MQTT_PASSWORD_LOCAL = umqtt.config.mqtt_password_local
MQTT_SSL_LOCAL = False   # set to False if using local Mosquitto MQTT broker
MQTT_SSL_PARAMS_LOCAL = {'server_hostname': MQTT_SERVER_LOCAL}

# MQTT Parameters for remote internet connection
MQTT_SERVER_REMOTE = umqtt.config.mqtt_server_remote
MQTT_PORT_REMOTE = umqtt.config.mqtt_port_remote
MQTT_USER_REMOTE = umqtt.config.mqtt_username_remote
MQTT_PASSWORD_REMOTE = umqtt.config.mqtt_password_remote
MQTT_SSL_REMOTE = False   # set to False if using local Mosquitto MQTT broker
MQTT_SSL_PARAMS_REMOTE = {'server_hostname': MQTT_SERVER_REMOTE}

# MQTT generic parameters
MQTT_CLIENT_ID = var.hostname.encode()
MQTT_KEEPALIVE = 7200

MQTT_ENDPOINTS = [
    {
        "name": "Local",
        "server": MQTT_SERVER_LOCAL,
        "port": MQTT_PORT_LOCAL,
        "user": MQTT_USER_LOCAL,
        "password": MQTT_PASSWORD_LOCAL,
        "ssl": MQTT_SSL_LOCAL,
        "ssl_params": MQTT_SSL_PARAMS_LOCAL,
    },
    {
        "name": "Remote",
        "server": MQTT_SERVER_REMOTE,
        "port": MQTT_PORT_REMOTE,
        "user": MQTT_USER_REMOTE,
        "password": MQTT_PASSWORD_REMOTE,
        "ssl": MQTT_SSL_REMOTE,
        "ssl_params": MQTT_SSL_PARAMS_REMOTE,
    },
]

last_mqtt_endpoint = 0   # 0 = local first, 1 = remote first

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

def make_client(ep):
    return MQTTClient(
        client_id=MQTT_CLIENT_ID,
        server=ep["server"],
        port=ep["port"],
        user=ep["user"],
        password=ep["password"],
        keepalive=MQTT_KEEPALIVE,
        ssl=ep["ssl"],
        ssl_params=ep["ssl_params"],
    )

def connect_mqtt():
    global last_mqtt_endpoint

    order = [
        last_mqtt_endpoint,
        1 - last_mqtt_endpoint,
    ]

    last_error = None

    for idx in order:
        ep = MQTT_ENDPOINTS[idx]
        client = make_client(ep)
        try:
            log.info("Trying MQTT", ep["name"], ep["server"], ep["port"])
            client.connect()
            
            last_mqtt_endpoint = idx
            log.info("MQTT connected via", ep["name"])
            return client, ep["name"]

        except Exception as e:
            last_error = e
            log.warning("MQTT", ep["name"], "failed:", e)

            try:
                client.disconnect()
            except Exception:
                pass

    raise OSError("Both MQTT endpoints failed: " + str(last_error))

async def mqtt_task(period = 1.0):
    #Init
    client = None
    
    DISCOVERY_PREFIX = "homeassistant"
    BASE_TOPIC = "custom_sensors/" + var.hostname

    DEVICE_ID = var.hostname
    DEVICE_NAME = "CO2 Gen2 Sensor"

    device = {
        "identifiers": [DEVICE_ID],
        "name": DEVICE_NAME,
        "manufacturer": "David Dudas",
        "model": DEVICE_NAME,
    }

    def _pub(client, topic: str, payload: dict, retain: bool = True):
        #log.error(client)
        #log.error(topic)
        #log.error(payload)
        #log.error(retain)
        client.publish(topic.encode(), json.dumps(payload).encode(), retain=retain)

    # ----- Helpers to create entity payloads -----
    def sensor(unique_id, name, state_topic, unit=None, device_class=None, icon=None):
        p = {
            "name": name,
            "state_topic": state_topic,
            "unique_id": unique_id,
            "device": device,
        }
        if unit is not None:
            p["unit_of_measurement"] = unit
        if device_class is not None:
            p["device_class"] = device_class
        if icon is not None:
            p["icon"] = icon
        return p

    def binary_sensor(unique_id, name, state_topic, device_class=None,
                      payload_on="1", payload_off="0", icon=None):
        p = {
            "name": name,
            "state_topic": state_topic,
            "unique_id": unique_id,
            "device": device,
            "payload_on": payload_on,
            "payload_off": payload_off,
        }
        if device_class is not None:
            p["device_class"] = device_class
        if icon is not None:
            p["icon"] = icon
        return p

    def publish_discovery(client):
        """
        Publish HA MQTT discovery config for all sensors.
        Call once at boot (or after MQTT reconnect). Uses retain=True.
        """

        # ----- Publish discovery configs (retain=True) -----

        # CO2 level (ppm)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_co2/config",
             sensor(f"{DEVICE_ID}_co2", "CO2 Level", f"{BASE_TOPIC}/co2_level",
                    unit="ppm", device_class="carbon_dioxide"))

        # CO2 peak (ppm)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_co2_peak/config",
             sensor(f"{DEVICE_ID}_co2_peak", "CO2 Peak Level", f"{BASE_TOPIC}/co2_peak_level",
                    unit="ppm", device_class="carbon_dioxide"))

        # Temperature (°C)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_temperature/config",
             sensor(f"{DEVICE_ID}_temperature", "Temperature", f"{BASE_TOPIC}/temperature",
                    unit="°C", device_class="temperature"))

        # Humidity (%)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_humidity/config",
             sensor(f"{DEVICE_ID}_humidity", "Humidity", f"{BASE_TOPIC}/humidity",
                    unit="%", device_class="humidity"))

        # Lux (lx)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_lux/config",
             sensor(f"{DEVICE_ID}_lux", "Illuminance", f"{BASE_TOPIC}/lux",
                    unit="lx", device_class="illuminance"))

        # Battery (%)
        _pub(client,
             f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}_battery/config",
             sensor(f"{DEVICE_ID}_battery", "Battery", f"{BASE_TOPIC}/battery",
                    unit="%", device_class="battery"))

        # Low battery (binary)
        _pub(client,
             f"{DISCOVERY_PREFIX}/binary_sensor/{DEVICE_ID}_low_battery/config",
             binary_sensor(f"{DEVICE_ID}_low_battery", "Low Battery", f"{BASE_TOPIC}/low_battery",
                           device_class="battery", payload_on="1", payload_off="0"))

        # CO2 detected (binary)
        # If you publish True/False instead of 1/0, change payload_on/off accordingly.
        _pub(client,
             f"{DISCOVERY_PREFIX}/binary_sensor/{DEVICE_ID}_co2_detected/config",
             binary_sensor(f"{DEVICE_ID}_co2_detected", "CO2 Detected", f"{BASE_TOPIC}/co2_detected",
                           icon="mdi:molecule-co2", payload_on="1", payload_off="0"))

    #Run
    while True:
        
        await var.wifi_ready_evt.wait()
        log.debug("Successful WiFi connection event received!")
        
        client = None
        
        try:
            log.debug("Connecting to MQTT server...")
            await asyncio.sleep(0.1)
            client, mqtt_name = connect_mqtt()
            var.mqqt_server_connection = mqtt_name
            await asyncio.sleep(5)
            
            # Publish HA discovery with retain once after startup
            if var.first_connect:
                var.first_connect = False
                publish_discovery(client)
            
            if var.scd41_co2_detected is not None:
                client.publish(BASE_TOPIC+"/co2_detected", str(var.scd41_co2_detected))
            if var.sensor_data.co2_scd41 is not None:
                client.publish(BASE_TOPIC+"/co2_level", str(int(var.sensor_data.co2_scd41)))
            if var.scd41_co2_peak_ppm is not None:
                client.publish(BASE_TOPIC+"/co2_peak_level", str(int(var.scd41_co2_peak_ppm)))
            if var.sensor_data.temp_scd41 is not None:
                client.publish(BASE_TOPIC+"/temperature", f"{var.sensor_data.temp_scd41:.1f}")
            if var.sensor_data.humidity_scd41 is not None:
                client.publish(BASE_TOPIC+"/humidity", f"{var.sensor_data.humidity_scd41:.1f}")
            if var.sensor_data.lux_veml7700 is not None:
                if var.sensor_data.lux_veml7700 > 0.0001:
                    lux = var.sensor_data.lux_veml7700
                else:
                    lux = 0.0001
                client.publish(BASE_TOPIC+"/lux", f"{lux:.4f}")
            if var.system_data.bat_percentage is not None:
                client.publish(BASE_TOPIC+"/battery", str(int(var.system_data.bat_percentage)))
                low_battery = 0
                if var.system_data.bat_percentage < 20:
                    low_battery = 1
                client.publish(BASE_TOPIC+"/low_battery", str(low_battery))
                
            log.info("Successfuly published data to MQTT server")
                
            await asyncio.sleep(0.1)

        except Exception as e:
            log.error("MQTT publish failed:", e)
            var.mqqt_server_connection = "Server error"
            
        finally:
            if client:
                try:
                    log.debug("Disconnecting from MQTT server...")
                    client.disconnect()
                except Exception:
                    log.error("Disconnecting from MQTT server failed!")
                    pass

        await asyncio.sleep(period)
        
if __name__ == "__main__":
    print("TESTING SINGLE TASK!")
    asyncio.run(mqtt_task(10))