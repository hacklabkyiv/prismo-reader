#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 21:30:43 2019

@author: artsin
"""

import socket
import sys

MY_IP = '10.0.0.12'
READER_PORT = 9999

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
    connection.timeout(10)
    try:
        print('connection from', client_address)

        # Receive the data in small chunks and retransmit it
        while True:
            data += connection.recv(20).decode()
            if '\r\n' in data:
                print('sending data back to the client')
                #connection.sendall(data)
                print(data)
                try:
                    keyvalue = data.split("TAG:")[1].rstrip()
                    print(keyvalue)
                    # Allow anyone to unlock the reader
                    access = True
                    if access:
                        connection.sendall(b'ACCESS\n');
                    else:
                        connection.sendall(b'DENIED\n')
                except:
                    pass
                data = ""
            if not data:
                break
        connection.close()    
        print("Here")
                
    finally:
        # Clean up the connection
        connection.close()