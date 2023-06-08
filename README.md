# PRISMO readers
# (OUTDATED)

[Protocol description](./doc/protocol.md)
### Flashing instructions

Connect your reader to your USB-UART converter:

```
READER	USB-UART
5V 		-> 5V
GND		-> GND
RX		-> TX
TX		-> RX
RESET	-> RTS
FLASH	-> DTR
```

### HW test

After flashing your device, you can test your hardware. To do this, uncomment `HW_TEST` in `settings.h` file and flash this firmware. In serial monitor, with key is near the RFID frame (baudrate 9600) you should get something like this:

```
------ HW TEST STARTED --------
17:38:34.011 -> ------ HW TEST STARTED --------
17:38:37.001 -> 33384541313932323930304532333845413139323239303045323338454131393232393030453233384541313932323930304532333845413139323239303045323338454131393232393030453233384541
17:38:40.620 -> ------ HW TEST STARTED --------
17:38:43.608 -> ------ HW TEST STARTED --------

```

### Connection test with test server

Comment back `HW_TEST` in `settings.h` and specify network settings there.

```
STASSID	- name of your wifi network
STAPSK 	- password to your wifi network
HOST 	- IP address to your test server.
PORT	- Unique port of your reader
```

In `test_server.py` choose right `MY_IP` - IP of machine where `test_server.py` running and `READER_PORT`.