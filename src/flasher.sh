#!/bin/bash

# Define functions
function erase_flash() {
  local port="$1"
  local esptool="$2"

  echo "Erasing flash..."
  if python3 $esptool --chip esp32 --port "$port" erase_flash; then
    echo "ERASE: OK"
  else
    echo "ERASE: Fail"
    exit 1
  fi
}

function flash_firmware() {
  local port="$1"
  local esptool="$2"
  local firmware_file="$3"

  echo "Flashing MicroPython firmware..."
  if python3 $esptool --chip esp32 --port "$port" --baud 460800 write_flash -z 0x1000 "$firmware_file"; then
    echo "FLASH FIRMWARE: OK"
  else
    echo "FLASH FIRMWARE: Fail"
    exit 1
  fi
}

function upload_source_code() {
  local port="$1"

  echo "Uploading source code..."
  for file in ./*.py; do
    if [[ -f "$file" ]]; then
      echo "Uploading $file..."
      if ampy --port "$port" put "$file"; then
        echo "UPLOAD SOURCE CODE: OK"
      else
        echo "UPLOAD SOURCE CODE: Fail"
        exit 1
      fi
    fi
  done
}

function upload_config() {
  local port="$1"

  echo "Uploading source code..."
  
  if ampy --port "$port" put config.json; then
    echo "UPLOAD CONFIG FILE: OK"
  else
    echo "UPLOAD CONFIG FILE: Fail"
    exit 1
  fi
}

function connect_and_wait_for_boot() {
  local port="$1"
  local esptool="$2"
  echo "Reset device"
  if python3 $esptool run; then
    echo "RUN OK"
  else
   echo "RUN: Fail"
    exit 1
  fi

  sleep 1

  stty -F "$port" 115200 -echo -icrnl raw
  while read -r line; do
  echo "$line"

  if [[ "$line" == *"<UPDATE KEYS OK>"* ]]; then
    echo "FIRST BOOT: OK"
    exit 0
  fi

  if [[ "$line" == *"<UPDATE KEYS FAILED>"* ]]; then
    echo "FIRST BOOT: FAIL"
    exit 1
  fi
  done < "$port"
}

# Define variables
PORT="/dev/ttyUSB0"
ESPTOOL="/home/artsin/Dev/esptool/esptool.py"
FW_FILE="../fw/ESP32_GENERIC-20231005-v1.21.0.bin"
SRC_DIR="src"

# Call functions
erase_flash "$PORT" "$ESPTOOL"
flash_firmware "$PORT" "$ESPTOOL" "$FW_FILE"
upload_source_code "$PORT"
upload_config "$PORT"
connect_and_wait_for_boot "$PORT" "$ESPTOOL"
