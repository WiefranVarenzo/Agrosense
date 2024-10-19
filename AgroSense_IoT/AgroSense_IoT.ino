//-----Felix Rafel
#include "DHTesp.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <PubSubClient.h>
#include <WiFi.h>

#define DHT_PIN 27
#define TEMP_SENSOR_PIN 18
#define LDR_PIN 13
#define PH_PIN 35
#define MQ135_SENSOR_PIN 34
#define TDS_SENSOR_PIN 32  // Define TDS sensor pin
#define LED_PIN 19

// WiFi and MQTT settings
const char* ssid = "Kecoa Berdansa";
const char* password = "Berbahagialah1";
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* mqtt_topic_air = "csm3313_umt/group09/airquality";
const char* mqtt_topic_temp = "csm3313_umt/group09/temperature";
const char* mqtt_topic_humidity = "csm3313_umt/group09/humidity";
const char* mqtt_topic_tds = "csm3313_umt/group09/tds";
const char* mqtt_topic_ph = "csm3313_umt/group09/ph";
const char* mqtt_topic_light = "csm3313_umt/group09/light";
const char* mqtt_led_topic = "csm3313_umt/group09/led01";

WiFiClient espClient;
PubSubClient client(espClient);

// DHT sensor
DHTesp dht;

// DS18B20 sensor
OneWire oneWire(TEMP_SENSOR_PIN);
DallasTemperature DS18B20(&oneWire);

void setup_wifi() {
  Serial.begin(115200);
  Serial.println();
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
}
//-----Jessica Valencia
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
      client.subscribe(mqtt_led_topic);  // Subscribe to LED control topic
    } else {
      Serial.print("failed, try again in 5 seconds");
      delay(5000);
    }
  }
}

void handleLedControl(String payload) {
  if (payload == "ON") {
    digitalWrite(LED_PIN, HIGH);
  } else if (payload == "OFF") {
    digitalWrite(LED_PIN, LOW);
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  if (String(topic) == mqtt_led_topic) {
    handleLedControl(message);
  }
}

void setup() {
  // Initialize Serial, WiFi, and MQTT
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // Initialize sensors
  dht.setup(DHT_PIN, DHTesp::DHT22);
  DS18B20.begin();
  pinMode(LDR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(PH_PIN, INPUT);
  pinMode(TDS_SENSOR_PIN, INPUT);

  Serial.println();
  delay(1000);
}
//-----Wiefran Varenzo
void loop() {
  // Reconnect to MQTT if necessary
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // DHT sensor
  float temperature = dht.getTemperature();
  float humidity = dht.getHumidity();
  Serial.print("Temperature: ");
  Serial.print(temperature, 2); // Print with 2 decimal places
  Serial.println("°C");
  Serial.print("Humidity: ");
  Serial.print(humidity, 2); // Print with 2 decimal places
  Serial.println("%");

  // DS18B20 sensor
  DS18B20.requestTemperatures();
  float tempC = DS18B20.getTempCByIndex(0);
  Serial.print("DS18B20 Temperature: ");
  Serial.print(tempC, 2); // Print with 2 decimal places
  Serial.println("°C");

  // LDR sensor
  int lightState = digitalRead(LDR_PIN);
  String lightLevel = lightState == HIGH ? "Dark" : "Light";
  Serial.println(lightLevel);

  // pH sensor
  int measurings = 0;
  for (int i = 0; i < 10; i++) {
    measurings += analogRead(PH_PIN);
    delay(10);
  }
  float voltage = (3.3 / 4095.0 * measurings / 10);
  float phValue = -5.70 * voltage + 15.72; // Example calibration formula
  Serial.print("pH = ");
  Serial.println(phValue, 2); // Print with 2 decimal places

  // Air quality sensor
  int sensor_value = analogRead(MQ135_SENSOR_PIN);
  String air_quality_label = interpret_air_quality(sensor_value / 100);
  Serial.print("Air Quality Index: ");
  Serial.println(sensor_value / 100);
  Serial.print("Air Quality: ");
  Serial.println(air_quality_label);
//-----Jessica Theresia
  // TDS sensor
  int tdsValue = analogRead(TDS_SENSOR_PIN);
  float tdsVoltage = (tdsValue * 3.3) / 4095.0; // Convert to voltage
  float tdsPPM = (tdsVoltage * 133.42) / (1 + (tdsVoltage * 1.0094)); // Convert to ppm
  Serial.print("TDS Value: ");
  Serial.print(tdsPPM, 2); // Print with 2 decimal places
  Serial.println(" ppm");

  // Publish sensor data to MQTT
  client.publish(mqtt_topic_temp, String(temperature).c_str());
  client.publish(mqtt_topic_humidity, String(humidity).c_str());
  client.publish(mqtt_topic_light, lightLevel.c_str());
  client.publish(mqtt_topic_ph, String(phValue).c_str());
  client.publish(mqtt_topic_air, air_quality_label.c_str());
  client.publish(mqtt_topic_tds, String(tdsPPM).c_str());

  delay(2000);
}

String interpret_air_quality(int value) {
  if (value >= 0 && value <= 50) {
    return "Good";
  } else if (value >= 51 && value <= 100) {
    return "Moderate";
  } else if (value >= 101 && value <= 150) {
    return "Unhealthy for Sensitive Groups";
  } else if (value >= 151 && value <= 200) {
    return "Unhealthy";
  } else if (value >= 201 && value <= 300) {
    return "Very Unhealthy";
  } else if (value >= 301) {
    return "Hazardous";
  }
}