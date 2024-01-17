#!/bin/bash

# This script is used by Prismo server to automatically update reader firmware by its internal 
# Usage: flasher.sh device_id
# Define your variables below to be sure that script runs ok separately.
# For automated parsing of progress, there is system of tags, defined in code:
#   [STATUS: <status message>] - will be displayed as text on frontend
#   [PROGRESS: <percentage>] - will be displayed as progress bar


DEVICE_ID="$1" # Took from arguments
PORT="/dev/ttyUSB0"
ESPTOOL="python3 /home/artsin/Dev/esptool/esptool.py"
FW_FILE="../fw/ESP32_GENERIC-20231005-v1.21.0.bin"

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

function upload_source_code() {
  local port="$1"

  echo "[STATUS:Uploading source code]"
  for file in ./*.py; do
    if [[ -f "$file" ]]; then
      echo "Uploading $file..."
      if ampy --port "$port" put "$file"; then
        echo "[STATUS: UPLOAD $file OK]"
      else
        echo "[STATUS: UPLOAD $file FAILED]"
        exit 1
      fi
    fi
  done
}

function upload_config() {
  local port="$1"

  echo "[STATUS:Uploading config file]"
  
  if ampy --port "$port" put config.json; then
    echo "[STATUS:UPLOAD CONFIG FILE OK]"
  else
    echo "[STATUS:UPLOAD CONFIG FILE FAILED]"
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

  sleep 1

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
upload_source_code "$PORT"
echo "[PROGRESS:60]"
upload_config "$PORT"
echo "[PROGRESS:80]"
connect_and_wait_for_boot "$PORT" "$ESPTOOL"
echo "[PROGRESS:100]"
exit 0
