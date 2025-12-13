import config
import json
import requests
import usocket
from lib.keys_manager import KeysManager
from lib.network.url_parser import UrlParser
from lib.uping import ping

class _NetworkManager:
    parser: UrlParser = None
    def __init__(self):
        self.parser = UrlParser(config.HOST)
        print(config.HOST, " -> ", self.parser)

    def check_connection(self) -> bool:
        N_TRIES = 1
        hostname = self.parser.hostname
        port = self.parser.port if self.parser.port else 80
        try:
            ping_result = ping(hostname, count=N_TRIES, timeout=config.PING_TIMEOUT)
        except Exception as e:
            print("Ping failed due to: ", "Request error: ", e)
            return False

        # Number of tries should be the same as number of successful responses
        if ping_result == (N_TRIES, N_TRIES):
            print("PING server ok, check port")
            return self.__check_port(hostname, port)
        else:
            return False

    @staticmethod
    def __check_port(host, port, timeout=1):
        try:
            addr_info = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
            addr = addr_info[0][-1]
            s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect(addr)
            s.close()
            print(f"Port {port} is open on {host}")
            return True
        except OSError as e:
            # Error code 111 (ECONNREFUSED) often means port is closed
            # Other errors might indicate network issues or hostname resolution problems
            print(f"Error connecting to {host}:{port}")
            return False

    def report_key_use(self, key, operation) -> None:
        if not self.check_connection():
            print("PING server failed")
            return

        print("Report key use:", key, operation)
        url = "{}://{}/devices/{}/log_operation".format(self.parser.get_scheme, self.parser.netloc, config.DEVICE_ID)
        print("Request url:", url)
        try:
            json_payload = json.dumps({"operation": operation, "key": key})
            response = requests.post(url, headers={'content-type': 'application/json'}, data=json_payload, timeout=1)
            # You can handle the response here, for example, check for a successful status code.
            if response.status_code in [200, 201]:
                print("Request successful:", response.text)
            else:
                print("Request failed with status code:", response.status_code)
            response.close()
        except Exception as e:
            print("Request error:", e)

    def update_access_keys(self) -> bool:
        """
        Get new access keys from server. Return True if success
        """
        # To prevent wearing of flash memory, we check file content first. Also, we just read
        # keys when we are offline
        if not self.check_connection():
            print("PING server failed, use stored keys")
            return False

        url = "{}://{}/devices/{}/accesses/".format(self.parser.get_scheme, self.parser.netloc, config.DEVICE_ID)
        print("Request url:", url)
        try:
            print("Try update access keys")
            response = requests.get(url, timeout=3)
            print("Finish GET")
            if response.status_code == 200:
                # Write new data to file only if there is updates
                print("Access keys updated from server")
                KeysManager.save_keys(response.text)
                response.close()
                return True
            else:
                print("Cannot update access keys from server, code:", response.status_code)
                response.close()
                print("<UPDATE KEYS FAILED>")  # Tag about success boot, used by automatic flasher
                return False

        except Exception as e:
            print("Can't perform request to ", config.HOST, " Request error: ", e)
            print("<UPDATE KEYS FAILED>")  # Tag about success boot, used by automatic flasher
            return False

NetworkManager = _NetworkManager()