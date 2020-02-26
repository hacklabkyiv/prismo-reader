#include <ESP8266WiFi.h>
#include "rdm6300.h"
#include "settings.h"
#include "misc.h"

int rx_mux_pin = 12;
int relay_pin = 13;
int led_blue_pin = 5;
int led_red_pin = 4;
int buzzer_pin = 10;

Rdm6300 rdm6300;
WiFiClient client;

const char* host = HOST;
const uint16_t port = PORT;

void setup()
{
  pinMode(led_blue_pin, OUTPUT);
  pinMode(led_red_pin, OUTPUT);
  pinMode(buzzer_pin, OUTPUT);
  pinMode(rx_mux_pin, OUTPUT);
  pinMode(relay_pin, OUTPUT);
  // Mux UART RX to RDM6300 
  digitalWrite(rx_mux_pin, HIGH);
  Serial.begin(9600);
  rdm6300.begin(&Serial);
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
  client.keepAlive(100, 10, 6);
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

bool checkAccess(uint32_t tagId)
{
  String requestPrefix = "TAG:";
  String hashedTagValue = hashTag(tagId);
  client.println(requestPrefix + hashedTagValue);
  Serial.println(">>>> Request sent, hashed value is: " + hashedTagValue);
  String answer = client.readStringUntil('\n');
  Serial.println(">>>> Received from server: " + answer);
  if (answer.equals("ACCESS"))
    return ACCESS_GRANTED;
  else if (answer.equals("ACCESS"))
    return ACCESS_DENIED;
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
        unlockReader();
        state = WAIT_FOR_LOCK;
      } else if (requestResult == ACCESS_DENIED){
        Serial.println("Access denied by server!");
      }
    }
    // Check connection
    if (!client.connected()) {
      client.println("Connection with server lost, try to reconnect");
      state = CONNECTING_TO_SERVER; 
    }
    break;
  case WAIT_FOR_LOCK:
    if (rdm6300.update()) {
      uint32_t tag = rdm6300.get_tag_id();
      Serial.print("LOGOUT tag received: ");
      Serial.println(tag, HEX);
      client.println("LOGOUT");
      lockReader();
      state = WAIT_FOR_KEY;
    }
    break;
  case CONNECTING_TO_SERVER:
    if (WiFi.status() == WL_CONNECTED) {
      connectToServer();
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
