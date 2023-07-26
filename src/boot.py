"""
This file is executed on every boot (including wake-boot from deepsleep).
It is responsible for connecting to the Wi-Fi network.
"""
__author__ = "sashkoiv"
__copyright__ = "Copyright 2023, KyivHacklab"
__credits__ = ["artsin, sashkoiv, paulftw, lazer_ninja, Vova Stelmashchuk"]


import network
from config import STASSID, STAPSK, LED_QTY, COLORS
from machine import Pin
from time import sleep_ms
from neopixel import NeoPixel

led = Pin(4, Pin.OUT)
l = NeoPixel(led, LED_QTY)
l.fill((0,0,0))
l.write()

# def ledIndication(colors: dict=COLORS, led_qty: int=config.LED_QTY) -> None:
#     """
#     """
#     colors = [c for c in COLORS.keys()]
#     while
#     for r in range(255):
#         for g in range(255):
#             for b in range(255):
#                 l.fill((r,g,b))
#                 l.write()



wlan = network.WLAN(network.STA_IF) # create station interface
wlan.active(True)       # activate the interface

print('WLAN network to connect is: ', STASSID)

if not wlan.isconnected():
    print('connecting to network...')
    wlan.connect(STASSID, STAPSK) # connect to an AP
    while not wlan.isconnected():
        r=0
        g=0
        b=0

        for r in range(0,256,20):
            l.fill((r,g,b))
            l.write()
            sleep_ms(1)
        for g in range(0,256,20):
            l.fill((r,g,b))
            l.write()
            sleep_ms(1)
        for b in range(0,256,20):
            l.fill((r,g,b))
            l.write()
            sleep_ms(1)
l.fill((0,0,0))
l.write()


print('Network config:', wlan.ifconfig())
print('Device mac:', wlan.config('mac'))
