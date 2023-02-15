#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <ESPDateTime.h>


// Initilizing the pins for the sensor inputs
//const int obstacle_detect = D4;
const int bcv_button = D4;
const int pinIR2d = D7;
const int pinIR3d = D8;
const int trigPin = D6;
const int echoPin = D5;
const int motor_in1 = D0; 
const int motor_in2 = D1;
const int motor_in3 = D2;
const int motor_in4 = D3;

String control_command;
float distCm;

long now = millis();
long lastMeasure = 0;
int start_contrl = 0;
int button_contrl = 1;

#define SOUND_VELOCITY 0.034
#define CM_TO_INCH 0.393701


//Initilizing the wifi and mqtt necessary values
const char* ssid = "Thinesh netzwerk";
const char* password = "Feb@2021";

//const char* ssid = "OnePlus Nord";
//const char* password = "johnpravin";

const char* mqtt_topic = "BCV/esp8266_1/Sensor/Val";

const char* mqtt_start_topic = "BCV/esp8266_1/Control";

// Change the variable to your Raspberry Pi IP address, so it connects to your MQTT broker
const char* mqtt_server = "192.168.0.123";

// Initializes the espClient
WiFiClient espClient;
PubSubClient client(espClient);


void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("WiFi connected - ESP IP address: ");
  Serial.println(WiFi.localIP());
}


String callback(String topic, byte* message, unsigned int length) {

  //String messageTemp;
  control_command = "";
  
  for (int i = 0; i < length; i++) {
    //Serial.print((char)message[i]);
    control_command += (char)message[i];
  }
  //Serial.println();

  if (topic == mqtt_start_topic)
  { 
      Serial.print("Message arrived on topic: ");
      Serial.print(topic);
      Serial.print(". Message: ");
      Serial.println(control_command);
    }
  
  Serial.println();
  return control_command;
}


void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (client.connect("ESP8266Client")) {
      Serial.println("connected");  
      client.subscribe(mqtt_start_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(15000);
    }
  }
}

void setupDateTime() {
  // setup this after wifi connected
  // you can use custom timeZone,server and timeout
  // DateTime.setTimeZone(-4);
  //   DateTime.setServer("asia.pool.ntp.org");
  //   DateTime.begin(15 * 1000);
  DateTime.setServer("asia.pool.ntp.org");
  DateTime.setTimeZone("CET-1CEST,M3.5.0,M10.5.0/3");
  DateTime.begin();
  if (!DateTime.isTimeValid()) {
    Serial.println("Failed to get time from server.");
  } else {
    Serial.printf("Date Now is %s\n", DateTime.toISOString().c_str());
    Serial.printf("Timestamp is %ld\n", DateTime.now());
  }
}

void forward(){  //forword
  
//analogWrite(motor_speed, 100);

digitalWrite(motor_in1, LOW); //Right Motor backword Pin 

digitalWrite(motor_in2, HIGH);  //Right Motor forword Pin

digitalWrite(motor_in3, HIGH);  //Left Motor forword Pin 

digitalWrite(motor_in4, LOW); //Left Motor backword Pin  

}

void backward(){  //backward

//analogWrite(motor_speed, 100);

digitalWrite(motor_in1, HIGH); //Right Motor forword Pin 

digitalWrite(motor_in2, LOW);   //Right Motor backword Pin 

digitalWrite(motor_in3, LOW);  //Left Motor backword Pin

digitalWrite(motor_in4, HIGH); //Left Motor forword Pin 

Serial.println("Backward");

}

void turnRight(){ //turnRight

//analogWrite(motor_speed, 100);

digitalWrite(motor_in1, HIGH);  //Right Motor forword Pin 

digitalWrite(motor_in2, LOW); //Right Motor backword Pin  

digitalWrite(motor_in3, HIGH);  //Left Motor backword Pin 

digitalWrite(motor_in4, LOW); //Left Motor forword Pin 


}

void turnLeft(){ //turnLeft

//analogWrite(motor_speed, 100);

digitalWrite(motor_in1, LOW); //Right Motor forword Pin 

digitalWrite(motor_in2, HIGH);  //Right Motor backword Pin 

digitalWrite(motor_in3, LOW); //Left Motor backword Pin 

digitalWrite(motor_in4, HIGH);  //Left Motor forword Pin 


}

void Stop(){ //stop

//analogWrite(motor_speed, 100);

digitalWrite(motor_in1, LOW); //Right Motor forword Pin 

digitalWrite(motor_in2, LOW); //Right Motor backword Pin 

digitalWrite(motor_in3, LOW); //Left Motor backword Pin 

digitalWrite(motor_in4, LOW); //Left Motor forword Pin 

}


float ultrasonic_measure(){
    // Ultrasonic Sensor Value Init

    long duration;
    float distanceCm;
    
    //reading the ultrasonic values
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    
    // Sets the trigPin on HIGH state for 10 micro seconds
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    
    digitalWrite(trigPin, LOW);
    
    //Reads the echoPin, returns the sound wave travel time in microseconds
    duration = pulseIn(echoPin, HIGH);
    
    // Calculate the distance
    distanceCm = duration * SOUND_VELOCITY/2;
    
    return distanceCm;
    }


void measure_and_publish_value(String control_com){
      char buf[50];
      
      // to send the msg as json
      const int capacity = JSON_ARRAY_SIZE(2) + 4 * JSON_OBJECT_SIZE(2);
      StaticJsonDocument<capacity> doc;
      JsonObject BCV1_ESP8266 = doc.createNestedObject("BCV1_ESP8266");
      char esp_json[128];

        //String dt = DateTime.toString().c_str();
      distCm = ultrasonic_measure();
  
      // reading the IR values
      //float IR1valueD = digitalRead(pinIR1d);
      float IR2valueD = digitalRead(pinIR2d);
      float IR3valueD = digitalRead(pinIR3d);

      //time_t dt = DateTime.getTime();
      DateTime.toString().toCharArray(buf, 50);;

      BCV1_ESP8266["Timestamp"] = buf;
      BCV1_ESP8266["Ultrasonic_D_CM"]= distCm ;
      //BCV1_ESP8266["IR1_status"] = IR1valueD;
      BCV1_ESP8266["IR2_status"] = IR2valueD;
      BCV1_ESP8266["IR3_status"] = IR3valueD;
      //BCV1_ESP8266["Control"] = control_com;
 
      serializeJson(doc, esp_json);
      client.publish(mqtt_topic, esp_json, 2);
      Serial.println(esp_json);

}



void setup() {
  
  Serial.begin(115200);
  setup_wifi();
   
  //pinMode(pinIR1d, INPUT);
  pinMode(pinIR2d, INPUT);
  pinMode(pinIR3d, INPUT);
  pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
  pinMode(echoPin, INPUT);
  pinMode(bcv_button, INPUT);
  pinMode(motor_in1, OUTPUT);
  pinMode(motor_in2, OUTPUT);
  pinMode(motor_in3, OUTPUT);
  pinMode(motor_in4, OUTPUT);
  //pinMode(obstacle_detect, OUTPUT);

  //digitalWrite(obstacle_detect, LOW);
  
  digitalWrite(motor_in1, LOW); //Right Motor forword Pin 

  digitalWrite(motor_in2, LOW); //Right Motor backword Pin 
  
  digitalWrite(motor_in3, LOW); //Left Motor backword Pin 
  
  digitalWrite(motor_in4, LOW); //Left Motor forword Pin 
  
  client.setServer(mqtt_server, 1883);
  
  client.setCallback(callback);

  setupDateTime();
}

void loop() {
   button_contrl = digitalRead(bcv_button);
  
  if (!client.connected()) 
  {
    reconnect();
  }
  
  if(!client.loop())
  {
    client.connect("ESP8266Client");
  }

  if (control_command == "Start" || button_contrl == 0){
      now = millis();
      // Publishes new data every 100 milli seconds
      if (now - lastMeasure > 100) {
        lastMeasure = now;
        measure_and_publish_value(control_command);
        Serial.printf("Start");
        Serial.println("");
        control_command = "";
        start_contrl = 1;
      }
  }
     
   else if (control_command == "Forward"){
      now = millis();
      // Publishes new data every 100 milli seconds
      if (now - lastMeasure > 100) {
        lastMeasure = now;
        forward();
        measure_and_publish_value(control_command);
        Serial.printf("Forward");
        Serial.println("");
        control_command = "";
    }
   }
   else if (control_command == "Right"){
      now = millis();
      // Publishes new data every 100 milli seconds
      if (now - lastMeasure > 100) {
        lastMeasure = now;
        turnRight();
        measure_and_publish_value(control_command);
        Serial.printf("Right");
        Serial.println("");
        control_command = "";
    }
    }
    else if (control_command == "Left"){
      now = millis();
      // Publishes new data every 100 milli seconds
      if (now - lastMeasure > 100) {
        lastMeasure = now;
        turnLeft();
        measure_and_publish_value(control_command);
        Serial.printf("Left");
        Serial.println("");
        control_command = "";
    }
    }

    else if (control_command == "Stop"){
        Serial.printf("Stop");
        Serial.println("");
        start_contrl = 0;
       Stop();
    }
        
    else if (control_command == "Obstacle"){
        start_contrl = 0;
        Stop();
        Serial.printf("Obstacle Detected");
        Serial.println("");
        //digitalWrite(obstacle_detect, HIGH);
    }
    
  
}
