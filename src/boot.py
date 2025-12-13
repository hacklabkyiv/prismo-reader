"""
This file is executed on every boot (including wake-boot from deepsleep).
It is responsible for connecting to the Wi-Fi network.
"""
__author__ = "sashkoiv"
__copyright__ = "Copyright 2023, KyivHacklab"
__credits__ = ["artsin", "sashkoiv", "paulftw", "lazer_ninja", "Vova Stelmashchuk", "Sayorus"]


from lib.kernel import Kernel

Kernel.boot()