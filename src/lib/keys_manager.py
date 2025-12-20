import config
import json

class _KeysManager:
    __keys = []

    def has_access(self, key: str) -> bool:
        if len(self.__keys) == 0:
            self.__keys = self.get_access_keys()
            self.__keys.sort()

        return key in self.__keys

    @staticmethod
    def get_access_keys() -> list:
        """
        Get list of access keys, stored in local storage
        """
        keys = []
        try:
            with open(config.ACCESS_KEYS_FILE, "r") as file:
                content = file.read()
                # print("Read file ok:", content)
                json_data = json.loads(content)
                keys = json_data["keys"]
                # print("Allowed keys: ", json_data)

        except Exception as e:
            print("Cannot upload and parse stored keys, error:", e)

        return keys

    def save_keys(self, raw_keys):
        new_keys = json.loads(raw_keys)["keys"]
        new_keys.sort()
        if new_keys != self.__keys:
            try:
                # Open a file for writing the response content
                with open(config.ACCESS_KEYS_FILE, "w") as file:
                    file.write(raw_keys)
                print("Updated {} keys".format(len(new_keys)))
                self.__keys = new_keys

                print("<UPDATE KEYS OK>")  # Tag about success boot, used by automatic flasher
            except Exception as e:
                print("Cannot store keys, error:", e)



KeysManager = _KeysManager()