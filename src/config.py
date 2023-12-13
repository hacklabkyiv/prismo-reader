"""
Configuration for every use case of the reader.
"""
__author__ = "sashkoiv"
__copyright__ = "Copyright 2023, KyivHacklab"
__credits__ = ["artsin, sashkoiv, paulftw, lazer_ninja, Vova Stelmashchuk"]


import json

def get_config_data() -> dict:
    """
    Get 
    """

    json_data = {}
    try:
        with open("config.json", "r") as file:
            content = file.read()
            json_data = json.loads(content)
            #print("Read config file ok:", json_data)     
    except Exception as e:
        print("Cannot get stored config, error:", e)

    return json_data

stored_config = get_config_data()
print("Stored config: ", stored_config)
STASSID = stored_config["SSID"] 
STAPSK = stored_config["PSK"]

HOSTNAME = stored_config["HOSTNAME"]
HOST = stored_config["SERVER"] # in format "192.168.0.123:5000"
DEVICE_ID = stored_config['DEVICE_ID'] # in format "d2db5ec4-6e7a-11ee-b962-0242ac120002"

NFC_READ_TIMEOUT = 100
BEEP_ON = False # Because my cat is nervous during debugging
PING_TIMEOUT = 500 # In ms, check before making any request to prevent hangout
ACCESS_KEYS_FILE = "keys.json"
CHECK_TIME_SLEEP = 2
LED_QTY = 4
COLORS = {
    'none':     [0,0,0],
    'red':      [255, 0, 0],
    'orange':   [255, 127, 0],
    'yellow':   [255, 255, 0],
    'green':    [0, 255, 0],
    'blue':     [0, 0, 255],
    'indigo':   [75, 0, 130],
    'violet':   [148, 0, 211]
}
