"""
Configuration for every use case of the reader.
"""
__author__ = "sashkoiv"
__copyright__ = "Copyright 2023, KyivHacklab"
__credits__ = ["artsin, sashkoiv, paulftw, lazer_ninja, Vova Stelmashchuk"]


STASSID = "HackLab"
STAPSK = "derparol"

HOSTNAME = "TestingDevice"
HOST = "192.168.1.115"
# HOST = "192.168.88.220"
PORT = "9999"
MACHINE_NAME = "bigcnc"

HEARTBEAT_INTERVAL = 100000     # milliseconds

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
