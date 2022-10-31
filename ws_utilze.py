import os
import numpy as np
import json
from websocket import create_connection

global_stauts = None

def receive_global_status(general_status):
    global global_stauts
    global_stauts = general_status


# commu_ip = '192.168.2.217'
# commu_port = 11920

# rover_ip = '192.168.1.154'
# rover_port = 11920


# ws_rover = create_connection("ws://%s:%s/command"%(rover_ip,rover_port))
# ws_commu = create_connection("ws://%s:%s/command"%(commu_ip,commu_port))

def rover_do(joints, paras, speeds, ws_rover):
    label = 'move_multi'
    # joint 100: forward_backward
    # joint 101: up_down
    # joint 102: truning
    # joint 103: 
    # angle distance
    # ws = create_connection("ws://%s:%s/command"%(rover_ip,rover_port))

    # data = {"@class": "commu.message.MoveMultiInfo",
    #         "angles": paras,
    #         "client": 0,
    #         "commu": 0,
    #         "id": "",
    #         "joints":joints,
    #         "label": "move_multi",
    #         "room": "room",
    #         "speeds": speeds,
    #         "topic": "command"}

    data = {"@class": "commu.message.MoveMultiInfo",
            "angle": paras[-1],
            "client": 0,
            "commu": 0,
            "id": "",
            "joint":joints[-1],
            "label": "move",
            "room": "room",
            "speed": speeds[-1],
            "topic": "command"}
    if global_stauts["status"]!="stop":
        ws_rover.send(json.dumps(data))

    # pass


def move_multi_joint(joint, angle, speed, ws_commu):
    # ws = create_connection("ws://%s:%s/command"%(commu_ip,commu_port))

    # joints=[1,2,3,4]
    # angles=[10,20,30,30]
    # speeds=[10,20,30,30]

    data = {
    "@class":"commu.message.MoveMultiInfo",
    "label":"move_multi",
    "joints":joint,
    "angles":angle,
    "speeds":speed,
    "id":"",
    "topic":"command",
    "client":0,
    "room":"room",
    "commu":0
    }
    
    print("status",global_stauts["status"])
    if global_stauts["status"]!="stop":
        ws_commu.send(json.dumps(data))
    # result =  ws_commu.recv()
    # print("Received '%s'" % result)
    # ws.close()



def say_sentence(sentence, ws_commu):
    # ws = create_connection("ws://%s:%s/command"%(commu_ip,commu_port))

    data = {"@class":"commu.message.SayInfo",
    "label":"say",
    "text":sentence,
    # "voice":"eng_girl",
    "voice":"yuuto",
    "speed":1,"volume":1,"pitch":1,"pause":1000,
    "device":"default",
    "id":"",
    "topic":
    "command",
    "client":0,
    "room":"room",
    "commu":0}
    if global_stauts["status"]!="stop":
        ws_commu.send(json.dumps(data) )
    # result =  ws_commu.recv()
    # print("Received '%s'" % result)
    # ws.close()

def move_multi_joint_stop(joint, angle, speed, ws_commu):

    data = {
    "@class":"commu.message.MoveMultiInfo",
    "label":"move_multi",
    "joints":joint,
    "angles":angle,
    "speeds":speed,
    "id":"",
    "topic":"command",
    "client":0,
    "room":"room",
    "commu":0
    }
    
    ws_commu.send(json.dumps(data))