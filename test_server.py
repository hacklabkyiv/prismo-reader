#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "artsin, sashkoiv"
__copyright__ = "Copyright 2023, KyivHacklab"
__credits__ = ["artsin, sashkoiv, paulftw, lazer_ninja, Vova Stelmashchuk"]


import socket
import sys
import json

MY_IP = '192.168.88.220'
READER_PORT = 9999
db = {
    "u4xf5xfb+xc2x94/x11xa7x05]xc4?xa6xf9xcdQxf0xfbx83xc7xe4hxf8xcdxbaxe7xa4rxdcf":"grant",
    "{xecx81xe1xbax86x92xf1x9cx82x122Qx0fxd8&xc0x96YxccSxafx13(xa3x8dx1bx04x1ex03xe3g":"deny"
}
response = {
    "type": "response",
    "result": ""
}



# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = (MY_IP, READER_PORT)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

data = ""
while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = sock.accept()
    # connection.timeout(10)
    try:
        print('connection from', client_address)

        # Receive the data in small chunks and retransmit it
        while True:
            data += connection.recv(100).decode()
            if '\r\n' in data:
                try:
                    key = json.loads(data)['key']
                    res = db[key]
                except:
                    res = 'usernotfound'
                response['result'] = res
                # data
                print('sending data back to the client')
                connection.sendall((json.dumps(response)+'\r\n').encode('utf-8'))
                print(json.dumps(response).encode('utf-8'))
                data = ""
                break
            elif not data:
                break
        connection.close()
        print("Here")

    finally:
        # Clean up the connection
        connection.close()
