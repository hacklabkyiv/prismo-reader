"""
Main script is executed right after boot.py.
All the logic is scripted here.
"""
__author__ = "sashkoiv"
__copyright__ = "Copyright 2023, KyivHacklab"
__credits__ = ["artsin, sashkoiv, paulftw, lazer_ninja, Vova Stelmashchuk"]


from machine import Pin, SPI
from time import sleep, sleep_ms

import json
import hashlib

import PN532 as nfc
import config
import urequests as requests
from config import DEVICE_ID, HOST, BEEP_ON, NFC_READ_TIMEOUT

# Pins
buzzer = Pin(19, Pin.OUT, value=0)
relay = Pin(18, Pin.OUT, value=0)

# SPI
spi_dev = SPI(1, baudrate=1000000)
irq_pin = Pin(25, Pin.IN)
cs = Pin(2, Pin.OUT)
cs.on()

# SENSOR INIT
pn532 = nfc.PN532(spi_dev, cs)
ic, ver, rev, support = pn532.get_firmware_version()
print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()


def update_access_keys() -> list:
    """
    Get list of keys, allowed to open selected reader from server. Store them
    in separate file as json array.
    """
    KEY_FILE = "keys.json"

    json_data = []
    # To prevent wearing of flash memory, we check file content first. Also, we just read
    # keys when we are offline
    with open(KEY_FILE, "r") as file:
        content = file.read()
        try:
            json_data = json.loads(content)
            print("Allowed keys: ", json_data)
        except Exception as e:
            print("Cannot parse stored keys, error:", e)

    url = "http://{}/readers/user_with_access/{}".format(HOST, DEVICE_ID)
    try:
        response = requests.get(url)

        if response.status_code == 200:
            # Write new data to file only if there is updates
            new_json_data = json.loads(response.text)
            if new_json_data != json_data:
                # Open a file for writing the response content
                print("Access keys updated from server: ", response.text)
                with open(KEY_FILE, "w") as file:
                    file.write(response.text)
                response.close()
            json_data = new_json_data

        else:
            print("Cannot update access keys from server, code:", response.status_code)
            response.close()

    except Exception as e:
        print("Can't perform request to ", HOST, " Request error: ", e)

    return json_data


def report_key_use(key, operation) -> None:
    url = "http://{}/readers/{}/{}/{}".format(HOST, operation, key, DEVICE_ID)
    response = None
    try:
        response = requests.post(url)
        # You can handle the response here, for example, check for a successful status code.
        if response.status_code == 200:
            print("Request successful")
        else:
            print("Request failed with status code:", response.status_code)
    except Exception as e:
        print("Request error:", e)
    finally:
        if response is not None:
            response.close()


def read_nfc(dev: PN532, tmot: int = 5000) -> bytearray:
    """
    Reads the tag and returns the code of the tag.
    Args:
        dev (PN532):    An object of the device class
        tmot (int):     Timeout for the tag to be read
    Returns:
        bytearray:      The data read from the tag
    """
    uid = dev.read_passive_target(timeout=tmot)
    if uid is None:
        return None
    else:
        numbers = [i for i in uid]
        print("Raw data:", uid)
        print("Found card with UID:", [hex(i) for i in uid])
        return uid


def beep(qty: int = 1, long: bool = False) -> None:
    """
    Producing a beep sound on an active buzzer.
    Args:
        qty (int):      how many beeps will be produced
        long (bool):    True for long beeps
    """
    time_delay = 50
    if long:
        time_delay = 500

    for i in range(qty):
        buzzer.value(1)
        sleep_ms(time_delay)
        buzzer.value(0)
        if i != qty:
            sleep_ms(time_delay)


def led_indication(color: str, led_qty: int = config.LED_QTY) -> None:
    """
    Provides light indication of the event or status.
    Args:
        color (str):    color from the list of supported {config.COLORS.keys()}
        led_qty (int):  quantity of WS2812 diodes in string
    """
    if color in config.COLORS.keys():
        color_code = config.COLORS.get(color)
        l.fill(color_code)
        l.write()
    else:
        print("Unsupported color for indication, please select from the list:")
        print(config.COLORS.keys())


def unlock() -> None:
    """
    Grant access routine
    """
    relay.value(0)
    led_indication("green")
    if BEEP_ON:
        beep(2, False)


def lock() -> None:
    """
    Deny access routine
    """
    relay.value(1)
    led_indication("red")
    if BEEP_ON:
        beep(1, True)


def deny() -> None:
    """
    Operationn denied. Indicate the issue.
    Sounds as X in Morse
    """
    led_indication("indigo")
    if BEEP_ON:
        beep(1, True)
        beep(2, False)
        beep(1, True)
    sleep_ms(1000)
    led_indication("red")


# Enum-like states, since micropython does not have enums
class ReaderState:
    LOCKED = 1
    UNLOCKED = 2


lock()
state = ReaderState.LOCKED
access_keys_list = update_access_keys()

while True:
    key = read_nfc(pn532, NFC_READ_TIMEOUT)
    if key is None:
        continue
    hashed_key = hashlib.sha256(key).digest().hex()
    print("Check key: ", hashed_key)
    if (state is ReaderState.LOCKED) and (hashed_key in access_keys_list):
        unlock()
        state = ReaderState.UNLOCKED
        report_key_use(hashed_key, "start_work")
    elif (state is ReaderState.LOCKED) and (hashed_key not in access_keys_list):
        deny()
        report_key_use(hashed_key, "deny_access")
    elif state is ReaderState.UNLOCKED:
        lock()
        state = ReaderState.LOCKED
        report_key_use(hashed_key, "stop_work")
    # We update access key list every time when any key is detected.
    access_keys_list = update_access_keys()
