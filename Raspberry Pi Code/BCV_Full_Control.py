import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime
import random
import urllib.request as url
import requests
import grovepi
from grove_rgb_lcd import *
import math
import RPi.GPIO as GPIO

# Connect the Grove LED to digital port D3
obs_led = 4

# Connect the Button to digital port D4
button = 6

#the Servo Motor init
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
pwm = GPIO.PWM(18, 50)
pwm.start(7.5)
time.sleep(0.5)

# Grovepi Pinmode Setup
grovepi.pinMode(button,"INPUT")

# setting the LED to initial state
grovepi.digitalWrite(obs_led, 0)

app_domain = "https://abpas.herokuapp.com/"
start_command_list = ["raspPi/getRoboticInitiativeStates", "raspPi/getRetrievingState", "raspPi/receive", "raspPi/return"]

contrls_list = ["Start", "Forward", "Backward", "Right", "Left", "Stop"]
topic_sub_list = ["BCV/esp8266_1/Sensor/Val"]
topic_pub_list = ["BCV/esp8266_1/Control"]
domainfile = "domain.pddl"

def BCV_Ai_planner(BCV_value):
    start = 1
    ts = BCV_value["BCV1_ESP8266"]["Timestamp"]
    UltraSen = BCV_value["BCV1_ESP8266"]["Ultrasonic_D_CM"]
    IR2Sen = BCV_value["BCV1_ESP8266"]["IR2_status"]
    IR3Sen = BCV_value["BCV1_ESP8266"]["IR3_status"]
    
    out_lis = ["Is_Start s_val", "Is_Stop st_val", "Is_Right_IR r_val", "Is_Left_IR l_val", "Is_Both_IR b_val", "Is_Ultrasonic u_val", "Is_No_Ultrasonic u_val"]
    i=0

    problem_file = """(define (problem STOP_Action) (:domain ABPaS_domain)
    (:objects 
        l_val r_val u_val s_val bcv st_val t_val buzz_val exh_Val pir_val d_val b_val
    )
    """

    problem_file += """(:init
    """
    if start == 1:
        problem_file += "(" + out_lis[0] + ")" +"\n"

    if (UltraSen)>=10:
        problem_file += "(" + out_lis[6] + ")" +"\n"

    elif (UltraSen)<10:
        problem_file += "(" + out_lis[5] + ")" +"\n"

    if (IR2Sen == 1):
        if (IR3Sen == 1):
            problem_file += "(" + out_lis[1] + ")" +"\n"
        else:
            problem_file += "(" + out_lis[3] + ")" +"\n"
            
    else:
        if (IR3Sen == 0):
            problem_file += "(" + out_lis[4] + ")" +"\n"
        else:
            problem_file += "(" + out_lis[2] + ")" +"\n" 


    problem_file += """ )
    (:goal (or 
    (Obs_Detected bcv)
    (Move_Forward bcv)
    (Move_Stop bcv)
    (Move_Left bcv) 
    (Move_Right bcv) 
    )

    ))"""
    
    filename = "ABPaS_problem"

    with open(filename, "w") as f:
        f.write(problem_file)
    
    data = {'domain': open(domainfile, 'r').read(), 'problem': open(filename, 'r').read()}
    response = requests.post('http://solver.planning.domains/solve', json=data).json()
    return response

def BCV_Actuator(response):
    
    actresult = []
    contrl = ""
    
    for act in response['result']['plan']:
        step = act['name']
        actuations = step[1:len(step)-1].split(' ')
        actresult.append(actuations[0])
    
    print(actresult[0])
    
    if (actresult[0]=="forward_motion"):
        contrl = "Forward"
        
        #to control the servo motor as per the above action
        pwm.ChangeDutyCycle(11.5)
        time.sleep(0.5)
        #to control the obstacle detected LED as per the above action
        grovepi.digitalWrite(obs_led, 0)

    
    elif (actresult[0]=="right_motion"):
        contrl = "Right"
        
        #to control the servo motor as per the above action
        pwm.ChangeDutyCycle(11.5)
        time.sleep(0.5)
        #to control the obstacle detected LED as per the above action
        grovepi.digitalWrite(obs_led, 0)
            
    
    elif (actresult[0]=="left_motion"):
        contrl = "Left"
        #to control the servo motor as per the above action
        pwm.ChangeDutyCycle(11.5)
        time.sleep(0.5)
        #to control the obstacle detected LED as per the above action
        grovepi.digitalWrite(obs_led, 0)

    
    elif (actresult[0]=="stop_motion"):
        contrl = "Stop"
        #to control the servo motor as per the above action
        pwm.ChangeDutyCycle(7.5)
        time.sleep(0.5)
        #to control the obstacle detected LED as per the above action
        grovepi.digitalWrite(obs_led, 0)

    elif (actresult[0]=="obstacle_detected"):
        contrl = "Obstacle"
        #to control the obstacle detected LED as per the above action
        grovepi.digitalWrite(obs_led, 1)
    return contrl

def on_connect(client, userdata, flags, rc):
    print("connected!"+ str(rc))
    client.subscribe(topic_sub_list[0])
         
    
def on_message(client, userdata, msg):
    BCV_value = json.loads(msg.payload.decode())
    print(msg.topic + " "+str(BCV_value))
    response = BCV_Ai_planner(BCV_value)
    contrl = BCV_Actuator(response)
    print(contrl)
    client.publish(topic_pub_list[0], contrl, 2)

class mqtt_com:
    def __init__(self):
        self.mqttServer = "localhost"
        self.client = mqtt.Client()
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.connect(self.mqttServer, 1883, 60)
        
    def mqtt_publish(self, topic_pub_list, contrls):
        self.client.publish(topic_pub_list[0], contrls, 2)
        self.client.loop_forever()

ms = mqtt_com()

while True:
    start_button = grovepi.digitalRead(button)
    print("i am alive")
    if (start_button == 1):
        start = 1
        if start==1:
            ms.mqtt_publish(topic_pub_list = topic_pub_list, contrls = contrls_list[0])
    else:
        start = 0
'''
    try: 
        start_command_0 = url.urlopen(app_domain + start_command_list[0]).read().decode('utf8')
        start_command_1 = url.urlopen(app_domain + start_command_list[1]).read().decode('utf8')
        start_command_2 = url.urlopen(app_domain + start_command_list[2]).read().decode('utf8')
        start_command_3 = url.urlopen(app_domain + start_command_list[3]).read().decode('utf8')
    except:
        print('press button to proceed, internet is down')
        
        start_button = grovepi.digitalRead(button)
    #if (start_button == 1):
        
    if (start_command_0 or start_command_1 or start_command_2 or start_command_3 != "") or (start_button == 1):
        start = 1
        if start==1:
            ms.mqtt_publish(topic_pub_list = topic_pub_list, contrls_list = contrls_list)
    else:
        start = 0'''
         
    
