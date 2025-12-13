

class _Kernel:

    pixel = None
    external_watchdog = None
    wdt = None
    beeper = None
    relay = None
    logout_btn = None
    nfc = None

    def boot(self):
        from lib.boot import Boot
        Boot(self)

    def main(self):
        from lib.application import Application
        Application(self)

Kernel = _Kernel()