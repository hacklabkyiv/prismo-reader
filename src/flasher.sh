#!/bin/bash

# This script is used by Prismo server to automatically update reader firmware by its internal 
# Usage: flasher.sh device_id
# Define your variables below to be sure that script runs ok separately.
# For automated parsing of progress, there is system of tags, defined in code:
#   [STATUS: <status message>] - will be displayed as text on frontend
#   [PROGRESS: <percentage>] - will be displayed as progress bar


DEVICE_ID="$1" # Took from arguments
PORT="/dev/ttyUSB0"
ESPTOOL="esptool.py"
FW_FILE="../fw/ESP32_GENERIC-20240105-v1.22.1.bin"

# Define functions
function create_config_file() {
  local device_id="$1"

  # Get hostname from environment variable, otherwise use hostnamectl
  hostname="${HOST_HOSTNAME:-$(hostnamectl hostname)}"

  # Combine the hostname with ".local"
  hostname_local="$hostname.local:5000"

  # Get Wi-Fi SSID from environment variable, otherwise use nmcli
  wifi_ssid="${HOST_WIFI_SSID:-$(nmcli -s device wifi show-password | grep "SSID"| cut -d" " -f2)}"

  # Get Wi-Fi password from environment variable, otherwise use nmcli
  wifi_password="${HOST_WIFI_PASSWORD:-$(nmcli -s device wifi show-password | grep "Password"| cut -d" " -f2)}"

  echo "[STATUS:Creating config file]"

  # Build configuration data
  jo SSID=$wifi_ssid PSK=$wifi_password HOSTNAME=$hostname SERVER=$hostname_local DEVICE_ID=$device_id > config.json
  echo "[STATUS:CONFIG FILE CREATED]"
}

function erase_flash() {
  local port="$1"
  local esptool="$2"

  echo "[STATUS:Erasing flash]"
  if $esptool --chip esp32 --port "$port" erase_flash; then
    echo "[STATUS:ERASE OK]"
  else
    echo "[STATUS: ERASE FAILED]"
    exit 1
  fi
}

function flash_firmware() {
  local port="$1"
  local esptool="$2"
  local firmware_file="$3"

  echo "[STATUS: Flashing MicroPython firmware]"
  if $esptool --chip esp32 --port "$port" --baud 460800 write_flash -z 0x1000 "$firmware_file"; then
    echo "[STATUS:FLASH FIRMWARE OK]"
  else
    echo "[STATUS:FLASH FIRMWARE FAILED]"
    exit 1
  fi
}

function upload_source_code_and_config() {
  local port="$1"

  echo "[STATUS:Uploading source code and config]"
  if rshell -p "$port" "cp *.py /pyboard/; cp config.json /pyboard/"; then
    echo "[STATUS:UPLOAD OK]"
  else
    echo "[STATUS: UPLOAD FAILED]"
    exit 1
  fi
}

function connect_and_wait_for_boot() {
  local port="$1"
  local esptool="$2"
  echo "[STATUS: Reset device]"
  if $esptool run; then
    echo "[STATUS:RUN OK]"
  else
   echo "[STATUS:RUN DEVICE FAILED]"
    exit 1
  fi

  sleep 3

  stty -F "$port" 115200 -echo -icrnl raw
  while read -r line; do
  echo "$line"

  if [[ "$line" == *"<UPDATE KEYS OK>"* ]]; then
    echo "[STATUS:FIRST BOOT OK]"
    return 1
  fi

  if [[ "$line" == *"<UPDATE KEYS FAILED>"* ]]; then
    echo "[STATUS:FIRST BOOT FAILED]"
    exit 1
  fi
  done < "$port"
}


# Call functions
echo "[PROGRESS:5]"
create_config_file "$DEVICE_ID"
echo "[PROGRESS:10]"
erase_flash "$PORT" "$ESPTOOL"
echo "[PROGRESS:20]"
flash_firmware "$PORT" "$ESPTOOL" "$FW_FILE"
echo "[PROGRESS:40]"
upload_source_code_and_config "$PORT"
echo "[PROGRESS:60]"
connect_and_wait_for_boot "$PORT" "$ESPTOOL"
echo "[PROGRESS:100]"
exit 0
