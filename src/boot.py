"""
This file is executed on every boot (including wake-boot from deepsleep).
It is responsible for connecting to the Wi-Fi network.
"""
__author__ = "sashkoiv"
__copyright__ = "Copyright 2023, KyivHacklab"
__credits__ = ["artsin, sashkoiv, paulftw, lazer_ninja, Vova Stelmashchuk"]


import network
from config import STASSID, STAPSK

wlan = network.WLAN(network.STA_IF) # create station interface
wlan.active(True)       # activate the interface

if not wlan.isconnected():
    print('connecting to network...')
    wlan.connect(STASSID, STAPSK) # connect to an AP
    while not wlan.isconnected():
        pass
print('Network config:', wlan.ifconfig())
print('Device mac:', wlan.config('mac'))
