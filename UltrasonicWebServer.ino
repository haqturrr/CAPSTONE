#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>


// Replace with your network credentials
const char* ssid = "";
const char* password = "";

// Create AsyncWebServer object 
AsyncWebServer server(80);

// Create an Event Source on /events
AsyncEventSource events("/events");

// Timer variables
unsigned long lastTime = 0;  
unsigned long timerDelay = 5000;

// Static IP configuration
IPAddress local_IP(172, 20, 10, 10); 
IPAddress gateway(0, 0, 0, 0);         
IPAddress subnet(255, 255, 255, 0);    
IPAddress primaryDNS(0, 0, 0, 0);      
IPAddress secondaryDNS(0, 0, 0, 0);


// Create a sensor object
int trigPin1 = 13;
int echoPin1 = 12;
int trigPin2 = 14; 
int echoPin2 = 27;
int tiltPin = 26;
long duration1,duration2, cm1, cm2, distance, tilt;


void getSensorReadings(){

  digitalWrite(trigPin1, LOW);
  digitalWrite(trigPin2, LOW);

  delayMicroseconds(5);

  digitalWrite(trigPin1, HIGH);
  digitalWrite(trigPin2, HIGH);

  delayMicroseconds(10);

  digitalWrite(trigPin1, LOW);
  digitalWrite(trigPin2, LOW);


  if (digitalRead(tiltPin)== 0){

     duration1 = pulseIn(echoPin1, HIGH);
     cm1 = (duration1/2) / 29.1;
     distance = cm1;
     tilt = 0;

  }
  
  else{

     duration2 = pulseIn(echoPin2, HIGH);
     cm2 = (duration2/2) / 29.1;
     distance = cm2;
     tilt = 1;

  }


}

// Initialize WiFi
void initWiFi() {
    WiFi.mode(WIFI_STA);
    
    // Configure static IP
    if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
        Serial.println("Failed to configure static IP!");
    }
    
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi...");
    
    while (WiFi.status() != WL_CONNECTED) {
        Serial.print('.');
        delay(1000);
    }
    
  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
}

String processor(const String& var){
  getSensorReadings();


  return String(distance);

  return String(tilt);

  return String();
}

const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML>
  
  <html>

  <style>
    body {font-family: sans-serif;}
    h1 {text-align: center; font-size: 30px;}
    p {text-align: center; color: #4CAF50; font-size: 40px;}
  </style>
</head>
<body>
  <h1>Ultrasonic HC-SR 04 Distance Measurement</h1><br>
  <p>Distance in CM : <span id="dist">0</span> CM</p>
  <p>Tilt angle : <span id="tilt">0</span> degree </p>
 
<script>
if (!!window.EventSource) {
 var source = new EventSource('/events');
 
source.addEventListener('open', function(e) {
  console.log("Events Connected");
}, false);

source.addEventListener('error', function(e) {
  if (e.target.readyState != EventSource.OPEN) {
    console.log("Events Disconnected");
  }
}, false);

source.addEventListener('message', function(e) {
  console.log("message", e.data);
}, false);
 
 source.addEventListener('distance', function(e) {
  console.log("distance", e.data);
  document.getElementById("dist").innerHTML = e.data;
 }, false);

  source.addEventListener('tilt', function(e) {
  console.log("tilt", e.data);
  document.getElementById("tilt").innerHTML = e.data;
 }, false);

}
</script>
</body>
</html>)rawliteral";

void setup() {
  Serial.begin(115200);
  initWiFi();
  pinMode(trigPin1, OUTPUT);
  pinMode(trigPin2, OUTPUT);
  pinMode(echoPin1, INPUT);
  pinMode(echoPin2, INPUT);
  pinMode(tiltPin, INPUT);
 


  // Handle Web Server
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send_P(200, "text/html", index_html, processor);
  });
 
  // Handle Web Server Events
  events.onConnect([](AsyncEventSourceClient *client){
    if(client->lastId()){
      Serial.printf("Client reconnected! Last message ID that it got is: %u\n", client->lastId());
    }
    // send event with message "hello!", id current millis
    // and set reconnect delay to 1 second
    client->send("hello!", NULL, millis(), 10000);
  });
  server.addHandler(&events);

  server.begin();
}

void loop() {
  if ((millis() - lastTime) > timerDelay) {
    getSensorReadings();
    Serial.printf("Distance = %d cm \n", distance);
    Serial.printf("tilt = %d\n", tilt);
    Serial.println();

    // Send Events to the Web Client with the Sensor Readings
    
    events.send(String(distance).c_str(),"distance",millis());
    events.send(String(tilt).c_str(),"tilt",millis());
    
    
    lastTime = millis();
  }
}