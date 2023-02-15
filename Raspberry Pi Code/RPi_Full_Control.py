import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime
import grovepi
import math
import requests
import RPi.GPIO as GPIO
import random
import urllib.request as url
from grove_rgb_lcd import *


#init the mqtt Server and Connection
mqttServer = "localhost"

#DHT Sensor init
dht_sensor = 2  # The Sensor goes on digital port 2.

# Connect the Grove LED to digital port D3
p1_led = 3

# PIR Sensor init
pir1_sensor = 5
pir2_sensor = 6

#setting the dht sensor to initial state
dht_blue = 0    # The Blue colored sensor.

#setting the PIR sensor to initial state
PIR1_motion=0
PIR2_motion=0

# Relay Init
relay = 7

# Buzzer init
buzzer = 8

#LCD Init

setRGB(0,255,0)
setText("Wlcme to ABPAS!!")
time.sleep(1)

# setting the buzzer to initial state
grovepi.digitalWrite(buzzer,0)

# setting the LED to initial state
grovepi.digitalWrite(p1_led, 0)
    
# Grovepi Pinmode Setup
grovepi.pinMode(pir1_sensor,"INPUT")
grovepi.pinMode(pir2_sensor,"INPUT")
grovepi.pinMode(p1_led,"OUTPUT")
grovepi.pinMode(buzzer,"OUTPUT")
grovepi.pinMode(relay,"OUTPUT")


topic_pub_list = ["facility/RPi_Sensor/Values", "BCV/esp8266_1/Control"]
domainfile = "domain.pddl"

def RPi_Publish(topic, message):
    rpi_mqtt_pub = mqtt.Client("RPI_Sensor")
    rpi_mqtt_pub.connect(mqttServer, 1883, 70)
    rpi_mqtt_pub.loop_start()

    rpi_mqtt_pub.publish(topic, message, 2)
    
        
def RPi_Sensor():
    # Reading the Data from DHT Sensor
    [DHT_temp, DHT_humidity] = grovepi.dht(dht_sensor, dht_blue)
    
    # Reading PIR sensor Status
    PIR1_motion=grovepi.digitalRead(pir1_sensor)
    PIR2_motion=grovepi.digitalRead(pir2_sensor)
    
    # Reading the timstamp for logging
    dt = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    if str(DHT_temp) !="nan" and str(DHT_humidity) != "nan" and PIR1_motion !=255 and PIR2_motion !=255:
        
        message = {"RPi_Sensor": {
                   "Timestamp": dt,
                   "DHT_temp": DHT_temp,
                   "DHT_humidity": DHT_humidity,
                   "PIR1_motion": PIR1_motion,
                   "PIR2_motion": PIR2_motion
                                }
               }
    
        msg = json.dumps(message, indent=4)
        #start the publish
        RPi_Publish(topic = topic_pub_list[0], message = msg)
        
        
        #LCD Init
        setRGB(0,255,0)
        setText("Temp: " + str(DHT_temp) + " deg C" + "Hum: " + str(DHT_humidity) + "%")
    
    else:
        msg = ""
        
    return msg

def Rpi_Ai_planner(Rpi_value):
    start = 1
    Rpi_ts = Rpi_value["RPi_Sensor"]["Timestamp"]
    Rpi_temp = Rpi_value["RPi_Sensor"]["DHT_temp"]
    Rpi_hum = Rpi_value["RPi_Sensor"]["DHT_humidity"]
    Rpi_pir1 = Rpi_value["RPi_Sensor"]["PIR1_motion"]
    Rpi_pir2 = Rpi_value["RPi_Sensor"]["PIR2_motion"]
    
    out_lis = ["Is_Start s_val", "Is_Pir_Motion pir_val", "Is_No_Pir_Motion pir_val", "Is_HighTemp t_val", "Is_No_HighTemp t_val"]
    i=0

    problem_file = """(define (problem Rpi_problem) (:domain ABPaS_domain)
    (:objects 
        l_val r_val u_val s_val bcv st_val t_val buzz_val exh_Val pir_val d_val b_val
    )
    """

    problem_file += """(:init
    """
    if start == 1:
        problem_file += "(" + out_lis[0] + ")" +"\n"
        
    if Rpi_temp>27:
        problem_file += "(" + out_lis[3] + ")" +"\n"

    else:
        problem_file += "(" + out_lis[4] + ")" +"\n"
        
    if Rpi_pir1 == 1:
        problem_file += "(" + out_lis[1] + ")" +"\n"
    
    else:
        problem_file += "(" + out_lis[2] + ")" +"\n"

    problem_file += """ )
    (:goal (or 
    (Emermove_stop bcv)
    (Parking_Led_Glow pir_val)
    (All_Good_State bcv)
    )

    ))"""
    
    filename = "ABPaS_Rpi_problem"

    with open(filename, "w") as f:
        f.write(problem_file)
    
    data = {'domain': open(domainfile, 'r').read(), 'problem': open(filename, 'r').read()}
    response = requests.post('http://solver.planning.domains/solve', json=data).json()
    return response

def Rpi_Actuator(response):
    
    actresult = []
    for act in response['result']['plan']:
        step = act['name']
        actuations = step[1:len(step)-1].split(' ')
        actresult.append(actuations[0])
    
    print(actresult[0])
    
    if (actresult[0]=="all_good"):
        
        # Buzz for 1 second
        grovepi.digitalWrite(buzzer,0)
            
        # Relay on for 1 second
    
        grovepi.digitalWrite(relay, 0)
        contrl = "All Good"
        
        
        # P1_Led on for 1 second
        grovepi.digitalWrite(p1_led, 0)
    
    elif (actresult[0]=="pir_detection"):
        print("gotcha")
        contrl = "PIR movement"
        grovepi.digitalWrite(p1_led, 1)
        
    elif (actresult[0]=="emerstop_motion"):
        contrl = "Stop"
        
        # Buzz for 1 second
        grovepi.digitalWrite(buzzer,1)
        
    
        
        #LCD Init
        setRGB(255, 0,0)
        setText("High Temp Emergencyyyyy")
    
        
        if contrl == "Stop":
                RPi_Publish(topic = topic_pub_list[1], message = contrl)
        
        # Relay on for 1 second
        grovepi.digitalWrite(relay, 1)
        
    else:
        contrl = "no plans"
            
        
    return contrl

while True:
        msg = RPi_Sensor()
        print(msg)
        if msg != "":
            Rpi_value = json.loads(msg)
            response = Rpi_Ai_planner(Rpi_value)
            contrl = Rpi_Actuator(response)
            time.sleep(0.5)
    
    
    