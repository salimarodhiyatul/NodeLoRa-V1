//SENSOR SOIL HUMADITY
#include <esp_now.h>
#include <WiFi.h>

typedef struct {
  char node_id[6];
  char type[10];
  float value;
} SensorData;

SensorData dataSend;
uint8_t gatewayMac[] = {0x24,0x6F,0x28,0xAA,0xBB,0xCC}; //Ganti sesuai dengan Mac Addres ESP tujuan

#define SOIL_PIN 34

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  esp_now_init();

  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, gatewayMac, 6);
  peer.encrypt = false;
  esp_now_add_peer(&peer);

  strcpy(dataSend.node_id, "NODE1");
  strcpy(dataSend.type, "SOIL");
}

void loop() {
  int raw = analogRead(SOIL_PIN);
  dataSend.value = map(raw, 0, 4095, 0, 100);

  esp_now_send(gatewayMac, (uint8_t *)&dataSend, sizeof(dataSend));
  delay(5000);
}
