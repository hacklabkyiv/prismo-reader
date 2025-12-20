import network

import config
from config import STASSID, STAPSK, LED_QTY, HOSTNAME
from machine import Pin, WDT, SPI
from time import sleep_ms, sleep
from neopixel import NeoPixel
from lib.PN532 import PN532 as nfc
from lib.beeper import Beeper

class Boot:
    kernel = None
    def __init__(self, kernel):
        self.kernel = kernel
        self.boot()

    def boot(self):
        self.__init_pixel()
        self.__init_wifi()
        self.__init_watchdog()
        self.__init_beeper()
        self.__init_relay()
        self.__init_logout()
        self.__init_reader()
        self.kernel.beeper.play_melody("boot_ok")


    def __init_pixel(self):
        led = Pin(4, Pin.OUT)
        self.kernel.pixel = NeoPixel(led, LED_QTY)
        self.kernel.pixel.fill((0, 0, 0))
        self.kernel.pixel.write()
        self.kernel.external_watchdog = Pin(22, Pin.OUT, value=0)

    def __init_wifi(self):
        wlan = network.WLAN(network.STA_IF)  # create station interface
        wlan.active(True)  # activate the interface
        wlan.config(dhcp_hostname=HOSTNAME)
        print("WLAN network to connect is: ", STASSID)

        if not wlan.isconnected():
            print("Connecting to network...")
            wlan.connect(STASSID, STAPSK)  # connect to an AP
            while not wlan.isconnected():
                for j in range(256):
                    for q in range(3):
                        for i in range(0, 4, 3):
                            self.kernel.pixel.fill(self._wheel((i + j) % 255))
                            self.kernel.pixel.write()
                            sleep_ms(1)

                self.kernel.external_watchdog.value(int(not self.kernel.external_watchdog.value()))

        self.kernel.pixel.fill((0, 0, 0))
        self.kernel.pixel.write()
        self.kernel.external_watchdog.value(0)
        if wlan.isconnected():
            print("Network config:", wlan.ifconfig())
            print("Device mac:", ":".join([hex(i).replace("0x", "").upper() for i in wlan.config("mac")]))
        else:
            print("Cannot connect to WiFi, work in offline mode")

    def __init_watchdog(self):
        self.kernel.wdt = WDT(timeout=1 * 60_000)  # 1 min watchdog

    def __init_beeper(self):
        self.kernel.beeper = Beeper()

    def __init_relay(self):
        self.kernel.relay = Pin(18, Pin.OUT, value=0)

    def __init_logout(self):
        self.kernel.logout_btn = Pin(19, Pin.IN)

    def __init_reader(self):
        # SPI
        spi_dev = SPI(1, baudrate=1000000)
        irq_pin = Pin(25, Pin.IN, Pin.PULL_UP)
        rst_pin = Pin(16, Pin.OUT)
        cs = Pin(26, Pin.OUT)
        cs.off()
        sleep(1)
        cs.on()

        # SENSOR INIT
        while True:
            try:
                self.kernel.nfc = nfc(spi_dev, cs, reset=rst_pin)
                sleep(0.3)
                ic, ver, rev, support = self.kernel.nfc.get_firmware_version()
                print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))
                break
            except Exception as e:
                print("Cannot init PN532 due to: ", "Request error: ", e)
                sleep(1)
                print("Try again")

        # Configure PN532 to communicate with MiFare cards
        self.kernel.nfc.SAM_configuration()

    @staticmethod
    def _wheel(pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return pos * 3, 255 - pos * 3, 0
        elif pos < 170:
            pos -= 85
            return 255 - pos * 3, 0, pos * 3
        else:
            pos -= 170
            return 0, pos * 3, 255 - pos * 3