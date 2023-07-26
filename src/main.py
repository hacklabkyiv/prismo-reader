"""
Main script is executed right after boot.py.
All the logic is scripted here.
"""
__author__ = "sashkoiv"
__copyright__ = "Copyright 2023, KyivHacklab"
__credits__ = ["artsin, sashkoiv, paulftw, lazer_ninja, Vova Stelmashchuk"]


from machine import Pin, SPI, Timer
from time import sleep, sleep_ms
from neopixel import NeoPixel

import json
import socket
import hashlib

import PN532 as nfc
import config

# STATUS = !OPERATION
# For the cold start the status is locked and the operation request is to unlock
LOCK = "lock"
UNLOCK = "unlock"
OPERATION = UNLOCK

# Pins
buzzer = Pin(19, Pin.OUT, value=0)
relay = Pin(18, Pin.OUT, value=0)
led = Pin(4, Pin.OUT)
# GWIOT_RX = Pin(21)      # GWIOT_7941E_RX_PIN 21

# Timers for auto periodic processes
heartbeatTimer = Timer(0)

# SPI
spi_dev = SPI(1, baudrate=1000000)
irq_pin = Pin(25, Pin.IN)
cs = Pin(2, Pin.OUT)
cs.on()

# SENSOR INIT
pn532 = nfc.PN532(spi_dev,cs)
ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

# Configure PN532 to communicate with MiFare cards
pn532.SAM_configuration()


def read_nfc(dev: PN532, tmot: int=5000) -> bytearray:
    """
    Reads the tag and returns the code of the tag.
    Args:
        dev (PN532):    An object of the device class
        tmot (int):     Timeout for the tag to be read
    Returns:
        bytearray:      The data read from the tag
    """
    print('Reading...')
    uid = dev.read_passive_target(timeout=tmot)
    if uid is None:
        print('Not found, try again.')
        return None
    else:
        numbers = [i for i in uid]
        print('Raw data:', uid)
        print('Found card with UID:', [hex(i) for i in uid])
        return uid


def read(_) -> None:
        key = read_nfc(pn532)
        if key is not None:
            resolveAccess(key)
        sleep(1)

irq_pin.irq(read)

def hashTag(raw_data: bytearray) -> bytes:
    """
    Create a hash sum of the input value.
    Args:
        raw_data (bytearray):   bytearray to be transformed
    Returns:
        bytes:  the hash sum of the tag
    """
    bytes_data = ''.join(hex(i)[2:] for i in raw_data).encode('utf-8')
    hash_sum = hashlib.sha256(bytes_data).digest()
    result = str(hash_sum).replace('\\','')[2:-1]
    print('HASH is:', result)
    return result


def beep(qty: int=1, long: bool=False) -> None:
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


def ledIndication(color: str, led_qty: int=config.LED_QTY) -> None:
    """
    Provides light indication of the event or status.
    Args:
        color (str):    color from the list of supported {config.COLORS.keys()}
        led_qty (int):  quantity of WS2812 diodes in string
    """
    if color in config.COLORS.keys():
        l = NeoPixel(led, led_qty)
        color_code = config.COLORS.get(color)
        for i in range(config.LED_QTY):
            l[i] = color_code
        l.write()
    else:
        print("Unsupported color for indication, please select from the list:")
        print(config.COLORS.keys())


def unlock() -> None:
    """
    Grant access routine
    """
    global OPERATION, LOCK
    OPERATION = LOCK

    relay.value(0)
    ledIndication('green')
    beep(2, False)


def lock() -> None:
    """
    Deny access routing
    """
    global OPERATION, UNLOCK
    OPERATION = UNLOCK

    relay.value(1)
    ledIndication('red')
    beep(1, True)


def denied() -> None:
    """
    Operationn denied. Indicate the issue.
    Sounds as X in Morse
    """
    ledIndication('indigo')
    beep(1, True)
    beep(2, False)
    beep(1, True)


def sendToSocket(request: str) -> str:
    """
    Sends a request to the server and receives a response.
    Args:
        request (str): The request to send
    Returns:
        str: collects, concatenates and returns the response
    """
    print("Open TCP socket")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(socket.getaddrinfo(config.HOST, config.PORT)[0][-1])
        requestSize = s.send(request)
        print("Request of a ", requestSize, " bytes is sent")

        print("The response is:")
        data = ''
        while True:
            data += str(s.recv(100), 'utf8')    # Reading 100 bytes pieces
            print('receiving...')
            if data is '':
                print("No response received")
                break
            elif '\r\n' in data:                # Detect end of the packet
                print(data, end='')
                break
        print("Closing the socket.")
    except Exception() as e:
        print(e)
        print("Ooops, something went wrong ¯\_(ツ)_/¯.")
    finally:
        s.close()

    return data


def resolveAccess(key: bytes) -> None:
    """
    Sends the hash sum of the key to the server with a request.
    Depending on access rights of the key owner performs an action -
    either to grant access to the accessory or deny access.
    Args:
        key (bytes):        the value from the tag
    """
    global OPERATION, LOCK, UNLOCK
    print('Sending request...')
    hashResult = str(hashTag(key))

    if OPERATION == UNLOCK:
        print('to be unlocked')
    elif OPERATION == LOCK:
        print('to be locked')

    req = {"type":"request","operation":OPERATION,"id":config.MACHINE_NAME,"key":hashResult}
    request = json.dumps(req) + "\r\n"
    print("The access request is:\n", request)

    data = sendToSocket(request)

    if data:
        try:
            result = json.loads(data)['result']
        except:
            result = ''

    if OPERATION == UNLOCK and ("grant" in data):   # UNLOCK grant
        unlock()
        print("Access granted")
    elif OPERATION == UNLOCK and ("deny" in data):  # UNLOCK deny
        denied()
        print("Access denied")
    elif OPERATION == LOCK and ("confirmed" in data): # LOCK confirm
        lock()
        print("Access granted")
    else:
        print("Response is neither approve nor rejects the access.")
        print("Doing nothing")


def sendHeartbeat(_) -> None:
    """
    Sending heartbeat request to the server every {config.HEARTBEAT_INTERVAL}
    seconds so that the server doesn't count extra time of using the machine
    in case the reader is stuck and is not able to log out the user.
    """
    req = {"type":"heartbeat","id":config.MACHINE_NAME}
    request = json.dumps(req) + "\r\n"
    print("The heartbeat request is:\n", request)

    data = sendToSocket(request)
    print(data)


heartbeatTimer.init(period=config.HEARTBEAT_INTERVAL,
                    mode=Timer.PERIODIC,
                    callback=sendHeartbeat)

read(1) # First initial try to read before the interrupt can start working normally
