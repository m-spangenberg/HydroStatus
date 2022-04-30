/*
  Author: Marthinus Spangenberg - https://github.com/m-spangenberg
  Project: Water Meter - https://github.com/m-spangenberg
  
  Micro-Controller: WeMOS NodeMCU V3 with ESP8266
  Sensor: YF-B10 DN25 5V Turbine Flow Sensor
  Status LED: Common Anode Diffused RGB (Resistor Values - R:150R,G:100R,B:100R)
*/

#include <ESP8266WiFi.h>
#include <InfluxDbClient.h>

// Wireless Access
const char* ssid = "INSERTYOURSSID";
const char* pass = "INSERTYOURPASS";
const char* wifi_hostname = "INSERTYOURHOSTNAME";

// Initialize LED pins
#define RED 14  // D5
#define GREEN 12  // D6
#define BLUE 13  // D7

// Initialize Flow Sensor pin
#define SENSOR 4  // D2

// Initialize InfluxDB Credentials
#define INFLUXDB_URL "http://DBIPADDRESS:PORT"
#define INFLUXDB_DATABASE "INSERTYOURDATABASENAME"
#define INFLUXDB_USER "INSERTYOURDBUSER"
#define INFLUXDB_PASS "INSERTYOURDBUSERPASS"

// Initialize Client
InfluxDBClient client(INFLUXDB_URL, INFLUXDB_DATABASE);

// Initialize WiFi Client Library
// See: https://www.arduino.cc/en/Reference/WiFi101SSLClient
WiFiClient ESPclient;

// Initialize Variables
int flashcount = 0;
int flashspeed = 0;

// Initialize Sensor Variables
volatile byte pulse_count;
byte pulses_sec = 0;

// Initialize Flow Calculation Variables
unsigned long ms_current = 0;
unsigned long ms_previous = 0;
int interval = 1000;
float calibration = 6;
float flow_rate;
float flow_litres;
float total_litres;

// Pulse counting function that operates in RAM
void IRAM_ATTR pulse_counter()
{
  pulse_count++;
}

/*
LED STATUS INDICATORS
*/

// Status Indicator LED: Magic

// Status Indicator LED: Breathe
void status_LED_breathe(int flashcount) {
  for(int x=0; x < flashcount; x++) {
    // delay between flashes
    delay(1000);
    
    // set LED to off
    delay(20);
    analogWrite(RED, 255);
    analogWrite(GREEN, 255);
    analogWrite(BLUE, 255);
    
    // breathe in
    for(int i=255; i>0; i--) {
      delay(10);
      analogWrite(RED, i);
      analogWrite(GREEN, i);
      analogWrite(BLUE, i);
    }

    // set LED fully on
    delay(20);
    analogWrite(RED, 0);
    analogWrite(GREEN, 0);
    analogWrite(BLUE, 0);
    

    // breathe out
    for(int i=0; i<255; i++) {
      delay(10);
      analogWrite(RED, i);
      analogWrite(GREEN, i);
      analogWrite(BLUE, i);
    }

    // set LED to fully off
    delay(20);
    analogWrite(RED, 255);
    analogWrite(GREEN, 255);
    analogWrite(BLUE, 255);
  }
}

// Status Indicator LED: Green
void status_LED_green(int flashcount, int flashspeed) {
  for(int x=0; x < flashcount; x++) {
    // delay between flashes
    delay(flashspeed);
    
    // set LED to off
    analogWrite(RED, 255);
    analogWrite(GREEN, 255);
    analogWrite(BLUE, 255);

    // delay between flashes
    delay(flashspeed);

    // set LED to on
    analogWrite(RED, 255);
    analogWrite(GREEN, 0);
    analogWrite(BLUE, 255);
  }
}

// Status Indicator LED: Blue
void status_LED_blue(int flashcount, int flashspeed) {
  for(int x=0; x < flashcount; x++) {
    // delay between flashes
    delay(flashspeed);
    
    // set LED to off
    analogWrite(RED, 255);
    analogWrite(GREEN, 255);
    analogWrite(BLUE, 255);

    // delay between flashes
    delay(flashspeed);

    // set LED to on
    analogWrite(RED, 255);
    analogWrite(GREEN, 255);
    analogWrite(BLUE, 0);
  }
}

// Status Indicator LED: White
void status_LED_white(int flashcount, int flashspeed) {
  for(int x=0; x < flashcount; x++) {
    // delay between flashes
    delay(flashspeed);
    
    // set LED to off
    analogWrite(RED, 255);
    analogWrite(GREEN, 255);
    analogWrite(BLUE, 255);

    // delay between flashes
    delay(flashspeed);

    // set LED to on
    analogWrite(RED, 0);
    analogWrite(GREEN, 0);
    analogWrite(BLUE, 0);
  }
}

// Status Indicator LED: Red
void status_LED_red(int flashcount, int flashspeed) {
  for(int x=0; x < flashcount; x++) {
    // delay between flashes
    delay(flashspeed);
    
    // set LED to off
    analogWrite(RED, 255);
    analogWrite(GREEN, 255);
    analogWrite(BLUE, 255);

    // delay between flashes
    delay(flashspeed);

    // set LED to on
    analogWrite(RED, 0);
    analogWrite(GREEN, 255);
    analogWrite(BLUE, 255);
  }
}

// Status Indicator LED: Ultravoilet
void status_LED_uv(int flashcount, int flashspeed) {
  for(int x=0; x < flashcount; x++) {
    // delay between flashes
    delay(flashspeed);
    
    // set LED to off
    analogWrite(RED, 255);
    analogWrite(GREEN, 255);
    analogWrite(BLUE, 255);

    // delay between flashes
    delay(flashspeed);

    // set LED to on
    analogWrite(RED, 65);
    analogWrite(GREEN, 240);
    analogWrite(BLUE, 20);
  }
}

/*
COMMUNICATIONS
*/

// Wireless
// See: https://arduino-esp8266.readthedocs.io/en/latest/esp8266wifi/readme.html
void connect_wifi() {
  
  int reconnect_count = 0;
  WiFi.hostname(wifi_hostname);

  Serial.print("Device MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
    
    // status_LED_uv(2, 100);
    delay(1000);
    reconnect_count ++;

    if (reconnect_count > 20) {
      // status_LED_red(1, 250);
      Serial.println("Trouble connecting...");
    }
  }

  // Confirm Connection
  // status_LED_green(1, 250);
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// Serial Debug
void serial_debug() {
  Serial.begin(115200);
  
  // wait for serial connection
  while (!Serial) {
    ; 
  }
  
  Serial.println("");
  Serial.println("Serial connection established...");
  
}

/*
POWER MANAGEMENT
*/

// Power State
// Deep Sleep for 15 seconds, GPIO 16 (D0) <--> RESET
void power_state() {
  Serial.println("Going in deep sleep...");
  ESP.deepSleep(15e6);
}

/*
SENSOR READINGS
*/

// Water Flow
void flow(unsigned long ms_current) {
  
  if (ms_current - ms_previous > interval) {
    pulses_sec = pulse_count;
    pulse_count = 0;

    // Calculate the flow rate per second and the total consumption
    flow_rate = ((1000.0 / (millis() - ms_previous)) * pulses_sec) / calibration;
    ms_previous = millis();
    flow_litres = (flow_rate / 60);
    total_litres += flow_litres;
    
    // Print the flow rate for this second in litres / minute
    Serial.print("Rate: ");
    Serial.print(float(flow_rate));
    Serial.print("L/min ");
    Serial.print(total_litres);
    Serial.print(" Litres Total");
    Serial.println("");

    // Define data point for flow of water in litres per minute
    Point pointDevice("water");
    // Set tags and values
    pointDevice.addTag("sensor", "flowrate");
    pointDevice.addField("value", float(flow_rate));

    // Define data point for usage in litres per second
    Point pointDevice2("water");
    // Set tags and values
    pointDevice2.addTag("sensor", "usage");
    pointDevice2.addField("value", flow_litres);

    // Define data point for total litres flowed since wake cycle
    Point pointDevice3("water");
    // Set tags and values
    pointDevice3.addTag("sensor", "cycletotal");
    pointDevice3.addField("value", total_litres);
    
    // Write data
    client.writePoint(pointDevice);
    client.writePoint(pointDevice2);
    client.writePoint(pointDevice3);
    
  }
}

/*
EXECUTION
*/

// Initialize
// See: https://www.arduino.cc/reference/en/
void setup() {

  // Connect to Serial Console
  serial_debug();
  
  // LED pins
  pinMode(RED, OUTPUT);
  pinMode(GREEN, OUTPUT);
  pinMode(BLUE, OUTPUT);

  // Connect to WiFi
  connect_wifi();

  // Synchronize time with NTP servers and set timezone
  configTzTime("UTC+02", "pool.ntp.org", "time.nis.gov");

  // Disable SSL Certs
  client.setInsecure();
  
  // Configure InfluxDB client
  client.setConnectionParamsV1(INFLUXDB_URL, INFLUXDB_DATABASE, INFLUXDB_USER, INFLUXDB_PASS);

  // Sensor variables
  pulse_count = 0;
  flow_rate = 0.0;
  ms_previous = 0;

  // Measure the SENSOR pin when going from high to low
  attachInterrupt(digitalPinToInterrupt(SENSOR), pulse_counter, FALLING);
  
}

// Tasks
void loop() {

  // Read the sensor
  ms_current = millis();
  flow(ms_current);

}
