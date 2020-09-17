#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 16:42:23 2020

@author: artsin
"""

import asyncio
import json
import logging
import psycopg2 as psycopg
from psycopg2.extensions import AsIs
import yaml
from yaml import Loader
import datetime

CONFIG_FILE = 'config.cfg'
cfg = yaml.load(open(CONFIG_FILE, 'r'), Loader=Loader)

logging.basicConfig(filename='log.txt', level=logging.DEBUG)

def get_usage_file():
    dt = datetime.datetime.now()
    f = cfg['logging']['usage-file'] + '-%s-%s.txt' % (dt.year, dt.month)
    return f

def check_user(key, toolname):
    logging.debug("Get user for key: %s" % key)
    conn = psycopg.connect(user = cfg['db-config']['user'],
                                  password = cfg['db-config']['password'],
                                  host=cfg['db-config']['server'],
                                  port=cfg['db-config']['port'],
                                  database='visitors')
    c = conn.cursor()
    c.execute("SELECT %s, name  FROM users WHERE key=%s", (AsIs(toolname), key))
    result = c.fetchone()
    conn.close()
    logging.debug("Database query ok, result: %s" % (result, ))
    
    with open(cfg['logging']['latest-key-file'], 'w') as latest_key_file:
        latest_key_file.write(key)
    
    response = ''
    
    if result:
        logging.info("Access granted for %s" % result[1])
        dt = datetime.datetime.now()
        with open(get_usage_file(), 'a') as toolfile:
            toolfile.write(json.dumps({'timestamp': datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"), 
                                       'user': result[1],
                                       'tool': toolname,
                                       'result': 'granted',
                                        }, indent=2))
            toolfile.write(',\r\n')
        response = json.dumps({'type': 'response', 'result': 'grant'}).encode('utf-8') + b'\r\n'
    else:
        logging.info("Access denied")
        with open(get_usage_file(), 'a') as toolfile:
            toolfile.write(json.dumps({'timestamp': datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"), 
                                       'user': '-',
                                       'tool': toolname,
                                       'result': 'denied',
                                        }, indent=2))
            toolfile.write(',\r\n')
        response = json.dumps({'type': 'response', 'result': 'deny'}).encode('utf-8') + b'\r\n'
    return response

async def handle_request(reader, writer):
    data = await reader.readline()
    message = data.decode()
    addr = writer.get_extra_info('peername')
    logging.debug("Received %r from %r" % (message, addr)) 
    packet = json.loads(data)
    if packet['type'] == 'request' and packet['operation'] == "unlock":
        logging.info("UNLOCK REQUEST")
        response = check_user(packet['key'], packet['id'])
        logging.debug("Sending response: %s" % response)
        writer.write(response)
        await writer.drain()
    if packet['type'] == 'request' and packet['operation'] == "lock":
        logging.debug("LOCK REQUEST")
        response = json.dumps({'type': 'response', 'result': 'confirmed'}).encode('utf-8') + b'\r\n'
        logging.debug("Sending response: %s" % response)
        writer.write(response)
        logging.info("Logout")
        with open(get_usage_file(), 'a') as toolfile:
            toolfile.write(json.dumps({'timestamp': datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"), 
                                       'user': '-',
                                       'tool': packet['id'],
                                       'result': 'logout',
                                        }, indent=2))
            toolfile.write(',\r\n')
        await writer.drain()
    logging.debug("Close the client socket")
    writer.close()

loop = asyncio.get_event_loop()
coro = asyncio.start_server(handle_request, cfg['general']['host'], 
                            cfg['general']['port'], loop=loop)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
