//ESP GATEWAY
#include <esp_now.h>
#include <WiFi.h>

typedef struct {
  char node_id[6];
  char type[10];
  float value;
} SensorData;

SensorData rx;

void onRecv(const esp_now_recv_info *info,
            const uint8_t *data, int len) {
  memcpy(&rx, data, sizeof(rx));

  Serial.printf("%s|%s:%.2f\n",
                rx.node_id,
                rx.type,
                rx.value);
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  esp_now_init();
  esp_now_register_recv_cb(onRecv);
}

void loop() {}