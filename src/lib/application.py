import config
import hashlib
from time import sleep
from lib.PN532 import PN532
from lib.kernel import _Kernel
from lib.keys_manager import KeysManager
from lib.network.network_manager import NetworkManager
from lib.reader_state import ReaderState

class Application:
    __state = ReaderState.LOCKED
    def __init__(self, kernel: _Kernel):
        self.kernel = kernel
        self.run()


    def run(self):
        self.lock()

        NetworkManager.update_access_keys()

        while True:
            self.feed_watchdog()

            # Check if button was pressed to force logout
            if self.kernel.logout_btn.value() == 0:
                print("Logout button was pressed, force logout")
                if not self.is_locked():
                    self.lock()
                    sleep(0.1)
                    continue

            # Try to read card
            key = self.read_nfc(self.kernel.nfc, config.NFC_READ_TIMEOUT)

            # If no card was found, we continue to the next iteration
            if key is None:
                sleep(0.1)
                continue

            self.kernel.beeper.play_melody("got_key")
            self.led_indication("yellow")
            hashed_key = hashlib.sha256(key).digest().hex()
            print("Check key: ", hashed_key)
            # Here we do quick ping to check if server is reachable to prevent long wait.
            # This is because timeouts are not supported in requests mode.
            if self.is_locked() and KeysManager.has_access(hashed_key):
                self.unlock()
                NetworkManager.report_key_use(hashed_key, "unlock")
                # If device type is door, we need to wait delay and lock door again
                if config.DEVICE_TYPE == "door":
                    print("Door should be closed after delay")
                    sleep(config.DOOR_AUTOLOCK_TIME)
                    self.lock()

            elif self.is_locked() and not KeysManager.has_access(hashed_key):
                self.deny()
                NetworkManager.report_key_use(hashed_key, "deny_access")

            elif not self.is_locked():
                self.lock()
                NetworkManager.report_key_use(hashed_key, "lock")
            # We update access key list every time when any key is detected.
            NetworkManager.update_access_keys()
            sleep(config.CHECK_TIME_SLEEP)


    def feed_watchdog(self):
        # Feed watchdog to prevent hanging
        self.kernel.wdt.feed()
        self.kernel.external_watchdog.value(int(not self.kernel.external_watchdog.value()))

    def read_nfc(self, dev: PN532, timeout: int = 5000) -> bytearray | None:
        """
        Reads the tag and returns the code of the tag.
        Args:
            dev (PN532):    An object of the device class
            timeout (int):     Timeout for the tag to be read
        Returns:
            bytearray:      The data read from the tag
        """
        try:
            uid = dev.read_passive_target(timeout=timeout)
        except RuntimeError as e:
            self.kernel.beeper.play_melody("error")
            print("Read NFC error:", e)
            return None

        if uid is not None:
            print("Found card with UID:", [hex(i) for i in uid])

        return uid

    def led_indication(self, color: str) -> None:
        """
        Provides light indication of the event or status.
        Args:
            color (str):    color from the list of supported {config.COLORS.keys()}
        """
        if color in config.COLORS.keys():
            color_code = config.COLORS.get(color)
            self.kernel.pixel.fill(color_code)
            self.kernel.pixel.write()
        else:
            print("Unsupported color for indication, please select from the list:")
            print(config.COLORS.keys())


    def unlock(self) -> None:
        """
        Grant access routine
        """
        self.__state = ReaderState.UNLOCKED
        self.kernel.relay.value(1)
        self.led_indication("green")
        self.kernel.beeper.play_melody("unlock")

    def lock(self) -> None:
        """
        Deny access routine
        """
        self.__state = ReaderState.LOCKED
        self.kernel.relay.value(0)
        self.led_indication("red")
        self.kernel.beeper.play_melody("lock")

    def deny(self) -> None:
        """
        Operationn denied. Indicate the issue.
        Sounds as X in Morse
        """
        self.led_indication("indigo")
        self.kernel.beeper.play_melody("reject")
        self.led_indication("red")

    def is_locked(self) -> bool:
        return self.__state == ReaderState.LOCKED

