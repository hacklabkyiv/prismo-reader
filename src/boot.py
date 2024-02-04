"""
This file is executed on every boot (including wake-boot from deepsleep).
It is responsible for connecting to the Wi-Fi network.
"""
__author__ = "sashkoiv"
__copyright__ = "Copyright 2023, KyivHacklab"
__credits__ = ["artsin, sashkoiv, paulftw, lazer_ninja, Vova Stelmashchuk"]


import network
from config import STASSID, STAPSK, LED_QTY
from machine import Pin
from time import sleep_ms, ticks_ms
from neopixel import NeoPixel

led = Pin(4, Pin.OUT)
l = NeoPixel(led, LED_QTY)
l.fill((0, 0, 0))
l.write()

wlan = network.WLAN(network.STA_IF)  # create station interface
wlan.active(True)  # activate the interface

WIFI_CONNECT_TIMEOUT = 5000

print("WLAN network to connect is: ", STASSID)

if not wlan.isconnected():
    print("Connecting to network...")
    wlan.connect(STASSID, STAPSK)  # connect to an AP
    start_connection_time = ticks_ms()
    while not wlan.isconnected():
        r = 0
        g = 0
        b = 0

        for r in range(128, 256, 20):
            l.fill((r, g, b))
            l.write()
            sleep_ms(1)
        for g in range(50, 256, 20):
            l.fill((r, g, b))
            l.write()
            sleep_ms(1)
        for b in range(256, 256, 256):
            l.fill((r, g, b))
            l.write()
            sleep_ms(1)
        if ticks_ms() - start_connection_time > WIFI_CONNECT_TIMEOUT:
            print("WiFi connection timeout")
            break

l.fill((0, 0, 0))
l.write()

if wlan.isconnected():
    print("Network config:", wlan.ifconfig())
    print("Device mac:", wlan.config("mac"))
else:
    print("Cannot connect to WiFi, work in offline mode")
