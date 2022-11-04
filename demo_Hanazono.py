from pickle import TRUE
from ws_utilze import *
import time
from cylinder_movement import *
# from upbody_movements import *
from body_movement import *
import threading
import rospy
from geometry_msgs.msg import Twist
import numpy as np
import os
import asyncio
import websockets
import signal
import sys
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer, SimpleSSLWebSocketServer

#print('resetting the cylinder， will be finished in 5 sec ...')
#os.system('python3 Horizontal_reset.py')
# print('finished')

commu_ip = '192.168.100.122'
# commu_ip = '10.186.42.31'
commu_port = 11920
ws_commu = create_connection("ws://%s:%s/command"%(commu_ip,commu_port))


EMOTION = "talking"
SCALE = 0.5
SPEED = 0.2
status = "trun_around"
moving_time = 0

FO = 0
ENERGY = 0
F0_COM = 0
ENERGY_COM = 0
period = 0
MAX_TIME = 15
elapsed_time = 0
st = time.time()
status = "moving"
# status = "stop"
twist = None
UPPER_FLAG = True

global_status_dictionary = {
    "status": "moving"
}


def callback(twist_):
    global twist
    twist = twist_

def signal_handler(signal, frame):
        # close the socket here
        sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

rospy.init_node('emotional_walk')
# wsc-json-hanazono.pyでは capf_navigation ノードを作成します

pub = rospy.Publisher('rover_twist', Twist, queue_size=10)
rate = rospy.Rate(30)
sub =  rospy.Subscriber("rover_twist", Twist, callback)

global_status_defintion_outside(global_status_dictionary)


class SimpleEcho(WebSocket):
    def handleMessage(self):
        global EMOTION, status, SCALE,elapsed_time,st, moving_time, UPPER_FLAG
    # async for message in websocket:
        data = json.loads(self.data)
        print(data)
        if data["command"] == "change_state":
            status = data["status"]
            global_status_dictionary["status"] = data["status"]
            elapsed_time = 0
            if status=="stop":
                move_multi_joint_stop([5, 3, 4, 2, 7, 8, 1, 0, 6],
                                [0, 0, -90, -90, 0, 0, 0, 0, 0, 0],
                                [50,50,50,50,50,5,5,5,5], ws_commu)
            st = time.time()
            moving_time = 0
        elif data["command"]== "change_emotion":
            EMOTION = data["emotion"]
            moving_time = 0
        elif data["command"] == "change_scale":
            SCALE = data["scale"]
        elif data["command"] == "upper_flag":
            UPPER_FLAG = 1==data["upper_flag"]

    def handleConnected(self):
        print(self.address, "connected")

    def handleClose(self):
        print(self.address, "close")
    

def ws():
    server = SimpleWebSocketServer("0.0.0.0", 11925, SimpleEcho)
    server.serveforever()


def rover_thread():
    global period, elapsed_time, twist, status, EMOTION, SCALE, SPEED, moving_time, status
    twist = Twist()
    while not rospy.is_shutdown():
        cylinder_v, period = cylinderg_parameters(emotion = EMOTION, x = elapsed_time, speed = SPEED, scale=SCALE)
        # cylinder_v, period = cylinderg_parameters(emotion = 'neutral', x = elapsed_time, speed = SPEED, scale=SCALE)
        twist.linear.z = cylinder_v
        # twist.linear.x = 0.
        if status == "stop":
            for _ in range(10):
                twist.linear.z = -0.2
                # twist.linear.x = 0.
                pub.publish(twist)
                rate.sleep()
            twist.linear.z = 0
            twist.angular.z = 0

        if status == 'turn_around':
            # twist.linear.x = 0.
            if moving_time<150:
                twist.angular.z = 0.6
                moving_time += 1
            # elif moving_time>=150 and moving_time<350:
            #     twist.angular.z = -0.6
            #     moving_time += 1
            # elif moving_time<430:
            #     twist.angular.z = 0.6
            #     moving_time += 1
            elif moving_time>=150 and moving_time<280:
                twist.angular.z = -0.6
                moving_time += 1
            else:
                twist.angular.z = 0

        # if EMOTION=='talking':
        #     if moving_time<50:
        #         twist.linear.x = 0.1
        #         moving_time += 1
        #     else:
        #         twist.linear.x = 0

        # if EMOTION=='no_talking':
        #     if moving_time<50:
        #         twist.linear.x = -0.1
        #         moving_time += 1
        #     else:
        #         twist.linear.x = 0.

        pub.publish(twist)
        rate.sleep()

def robot_thread():
    global period, elapsed_time, EMOTION, status, SCALE, UPPER_FLAG, ws_commu
    # stop_conduct = False
    # commu_ip = '192.168.1.167'
    # commu_port = 11920
    # ws_commu = create_connection("ws://%s:%s/command"%(commu_ip,commu_port))
    while True:
        if status=="stop":
            # if not stop_conduct:
            #     move_multi_joint([5, 3, 4, 2, 7, 8, 1, 0, 6],
            #                     [0, 0, -90, -90, 0, 0, 0, 0, 0, 0],
            #                     [50,50,50,50,50,5,5,5,5], ws_commu)
            #     stop_conduct = True
            continue
        if UPPER_FLAG:
            print('**robot doing// period %f, time %f'%(period, elapsed_time))
            body_movements(f0 = FO,
                            energy = ENERGY,
                            period = period,
                            emotion = EMOTION,
                            f0_com = F0_COM,
                            eneragy_com = ENERGY_COM,
                            ws_commu = ws_commu,
                            scale = SCALE)

            # stop_conduct = False
            time.sleep(0.1)

def time_thread():
    global elapsed_time,st
    while True:
    #while elapsed_time<=MAX_TIME:
        et = time.time()
        elapsed_time = np.round((et - st),1)


T0 = threading.Thread(target=time_thread)
T1 = threading.Thread(target=rover_thread)
T2 = threading.Thread(target=robot_thread)
T_ws = threading.Thread(target=ws)

T0.start()
T1.start()
T2.start()
T_ws.start()

T0.join()
T1.join()
T2.join()
T_ws.join()

# commu_ip = '192.168.1.167'
# commu_port = 11920
# ws_commu = create_connection("ws://%s:%s/command"%(commu_ip,commu_port))
move_multi_joint_stop([5, 3, 4, 2, 7, 8, 1, 0, 6],
                [0, 0, -90, -90, 0, 0, 0, 0, 0, 0],
                [30,30,20,20,20,5,5,5,5], ws_commu)
