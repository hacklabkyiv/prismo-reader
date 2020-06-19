#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>
#include "rdm6300.h"
#include "settings.h"
#include "misc.h"

int rx_mux_pin = 12;
int relay_pin = 13;
int led_blue_pin = 4;
int led_red_pin = 5;
int buzzer_pin = 2;

unsigned long heartbeat_last_time = millis();

Rdm6300 rdm6300;
WiFiClient client;
DynamicJsonDocument packet(1024);

const char* host = HOST;
const uint16_t port = PORT;

void setup()
{
  pinMode(led_blue_pin, OUTPUT);
  pinMode(led_red_pin, OUTPUT);
  pinMode(buzzer_pin, OUTPUT);
  pinMode(rx_mux_pin, OUTPUT);
  pinMode(relay_pin, OUTPUT);
  digitalWrite(buzzer_pin, LOW);
  digitalWrite(led_red_pin, HIGH);
  // Mux UART RX to RDM6300 
  digitalWrite(rx_mux_pin, HIGH);
  Serial.begin(9600);
  rdm6300.begin(&Serial);
  Serial.println("Start initialization");
}

void denyBeep()
{
  digitalWrite(buzzer_pin, HIGH);
  delay(50);
  digitalWrite(buzzer_pin, LOW);
  delay(100);
  digitalWrite(buzzer_pin, HIGH);
  delay(50);
  digitalWrite(buzzer_pin, LOW);
}

void allowBeep()
{
  digitalWrite(buzzer_pin, HIGH);
  delay(50);
  digitalWrite(buzzer_pin, LOW);
}

void userNotFoundBeep()
{
  for (int i = 0; i < 3; i++)
  {
    digitalWrite(buzzer_pin, HIGH);
    delay(50);
    digitalWrite(buzzer_pin, LOW);
  }
}

void wifiConnect()
{
  Serial.print("Connecting to ");
  Serial.println(STASSID);

  /* Explicitly set the ESP8266 to be a WiFi-client, otherwise, it by default,
     would try to act as both a client and an access-point and could cause
     network-issues with your other WiFi-devices on your WiFi-network. */
  WiFi.mode(WIFI_STA);
  WiFi.hostname(HOSTNAME);
  WiFi.begin(STASSID, STAPSK);
  Serial.println("=============================");
  Serial.println("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected!");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("=============================");
}

void connectToServer()
{
  Serial.print("connecting to ");
  Serial.print(host);
  Serial.print(':');
  Serial.println(port);
  while (!client.connect(host, port)) {
    Serial.println("connection failed, try again");
    delay(1000);
  }
  //client.keepAlive(100, 10, 6);
  Serial.println("Connection successful!");
}

// TODO implement normal hash function, for example Adler32
String hashTag(uint32_t tag)
{
  char buf[7];
  // Encoded with secret patented Hacklab technology:)
  uint32_t sercret_code = (tag) ^ 0xFFFFFF ^ 0xC78DC7;
  sprintf(buf, "%02X%02X%02X",
        (uint8_t) ~((sercret_code >> 16) & 0xFF),
        (uint8_t) ~((sercret_code >> 8) & 0xFF),
        (uint8_t) ~( sercret_code  & 0xFF)
        );
  return String(buf);
}

int checkAccess(uint32_t tagId)
{
  String requestPrefix = "TAG:";
  String hashedTagValue = hashTag(tagId);
  StaticJsonDocument<200> doc;
  //client.println(requestPrefix + hashedTagValue);
  packet["type"] = "request";
  packet["operation"] = "unlock";
  packet["id"] = MACHINE_NAME;
  packet["key"] = hashedTagValue;
  Serial.print(F("Sending request..."));
  serializeJson(packet, client);
  client.write("\r\n");
  Serial.println(">>>> Request sent, hashed value is: " + hashedTagValue);
  String answer = client.readStringUntil('\n');
  Serial.println(">>>> Received from server: " + answer);
  DeserializationError error = deserializeJson(doc, answer);
  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.c_str());
    return UNKNOWN_ERROR;
  }
  if (doc["result"] == "grant")
    return ACCESS_GRANTED;
  else if (doc["result"] == "deny")
    return ACCESS_DENIED;
  else if (doc["result"] == "norecord")
    return USER_NOT_FOUND;
}

int logoutUser(uint32_t tagId)
{
  String requestPrefix = "TAG:";
  String hashedTagValue = hashTag(tagId);
  StaticJsonDocument<200> doc;
  //client.println(requestPrefix + hashedTagValue);
  packet["type"] = "request";
  packet["operation"] = "lock";
  packet["id"] = MACHINE_NAME;
  packet["key"] = hashedTagValue;
  Serial.print(F("Sending request..."));
  serializeJson(packet, client);
  client.write("\r\n");
  Serial.println(">>>> Request sent, hashed value is: " + hashedTagValue);
  String answer = client.readStringUntil('\n');
  Serial.println(">>>> Received from server: " + answer);
  DeserializationError error = deserializeJson(doc, answer);
  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.c_str());
    return UNKNOWN_ERROR;
  }
  if (doc["result"] == "confirmed")
    return LOGOUT_CONFIRMED;
}

void sendHeartbeat()
{
  StaticJsonDocument<200> doc;
  //client.println(requestPrefix + hashedTagValue);
  packet["type"] = "heartbeat";
  packet["id"] = MACHINE_NAME;
  Serial.print(F("Sending heartbeat..."));
  serializeJson(packet, client);
  client.write("\r\n");
  heartbeat_last_time = millis();
}
void unlockReader()
{
  digitalWrite(relay_pin,HIGH);
  digitalWrite(led_blue_pin, HIGH);
  digitalWrite(led_red_pin, LOW);
}

void lockReader()
{
  digitalWrite(relay_pin,LOW);
  digitalWrite(led_blue_pin, LOW);
  digitalWrite(led_red_pin, HIGH);
}
int state = WIFI_CONNECTION;
int previousState = WIFI_CONNECTION;
bool isUnlocked = false;

#ifdef HW_TEST
void loop()
{
  Serial.println("------ HW TEST STARTED --------");
  // Test LED blinking
  digitalWrite(led_blue_pin, HIGH);
  delay(500);
  digitalWrite(led_blue_pin, LOW);
  delay(500);
  digitalWrite(led_red_pin, HIGH);
  delay(500);
  digitalWrite(led_red_pin, LOW);
  delay(500);
  // Check Relay
  digitalWrite(relay_pin,HIGH);
  delay(500);
  digitalWrite(relay_pin,LOW);
  delay(500);
  // Read raw data from RDM6300 reader
  while (Serial.available() > 0) {    
          int incomingByte = Serial.read();
          Serial.print(incomingByte, HEX);
  }
}

#else
void loop()
{
  switch (state){
  case WAIT_FOR_KEY:
    if (rdm6300.update()) {
      uint32_t tag = rdm6300.get_tag_id();
      Serial.print("Tag received: ");
      Serial.println(tag, HEX);
      int requestResult = checkAccess(tag);
      if (requestResult == ACCESS_GRANTED) {
        Serial.println("Access granted by server!");
        allowBeep();
        unlockReader();
        isUnlocked = true;
        state = WAIT_FOR_LOCK;
        Serial.print("State changed to wait for lock ");
      } else if (requestResult == ACCESS_DENIED){
        Serial.println("Access denied by server!");
        denyBeep();
      } else if (requestResult == USER_NOT_FOUND) {
        // process user not found case
        userNotFoundBeep();
      }
    }
    // Check connection
    if (!client.connected()) {
      Serial.print("Connection with server lost, try to reconnect");
      state = CONNECTING_TO_SERVER;
    } else if ((millis() - heartbeat_last_time) > HEARTBEAT_INTERVAL) {
      sendHeartbeat();
    }
    break;
  case WAIT_FOR_LOCK:
  //Serial.print("Wait for lock request");
    if (rdm6300.update()) {
      uint32_t tag = rdm6300.get_tag_id();
      Serial.print("LOGOUT request");
      int requestResult = logoutUser(tag);
      if (requestResult == LOGOUT_CONFIRMED)
      {
        client.println("LOGOUT OK");
        lockReader();
        allowBeep();
        isUnlocked = false;
        state = WAIT_FOR_KEY;
      }   
    }
    // Check connection
    if (!client.connected()) {
      Serial.print("Connection with server lost, try to reconnect");
      state = CONNECTING_TO_SERVER;
    } else if ((millis() - heartbeat_last_time) > HEARTBEAT_INTERVAL) {
      sendHeartbeat();
    }
    break;
  case CONNECTING_TO_SERVER:
    if (WiFi.status() == WL_CONNECTED) {
      connectToServer();
      if (isUnlocked)
        state = WAIT_FOR_LOCK;
      else
        state = WAIT_FOR_KEY;
      
    } else {
      Serial.println("No WIFI connection, try to reconnect");
      state = WIFI_CONNECTION;
    }
    break;
  case WIFI_CONNECTION:
    wifiConnect();
    state = CONNECTING_TO_SERVER;
    break;
  default:
    break;
  }
}
#endif
