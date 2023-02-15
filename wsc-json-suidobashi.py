# coding: utf-8
#! /usr/bin/env python3

import sys
import socket
import time
import websocket
import threading
import select
import ssl
from datetime import datetime, timedelta
import json
import rel
import requests

# ナビゲーションのためのROSライブラリ
import rospy
import actionlib #SimpleActionClientを使うためのパッケージ
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import Twist

import random

# ❶ JetsonのIPを登録
jetsonIP = "10.186.42.91"
# jetsonIP = "192.168.100.8"

# ❷ ナビゲーションの移動先を登録
waypoints = [
    [(-0.0856163501739502,-1.0303490161895752,0.0),(0.0,0.0,0.310046576055206,0.9507213685809546)],
    [(0.7238894701004028,1.3077094554901123,0.0),(0.0,0.0,0.8294782812788812,0.5585389698907617)],
    [(2.9680113792419434,3.5968070030212402,0.0),(0.0,0.0,-0.9948838474732121,0.10102539303016063)],
    [(4.735930442810059,-1.3344614505767822,0.0),(0.0,0.0,0.7088722662418192,0.7053368770688141)],
    [(-2.658176898956299,-1.5030968189239502,0.0),(0.0,0.0,0.6529810901764967,0.7573742112535348)],
]


rospy.init_node('capf_navigation') #ノードの初期化
# demo_Hanazono.pyでは emotional_walk ノードを作成します

client = actionlib.SimpleActionClient('move_base', MoveBaseAction)    #サーバ名，型ともに利用するサーバと一致させる
client.wait_for_server()    #サーバーの応答を待つ
# listener.waitForTransform("map", "base_link", rospy.Time(), rospy.Duration(2.0))
ros_msg = "ROS:: wait_for_server ...."

# マニュアル移動用
moveBindings = {
    'cmd;Forward':(1,0,0,0),
    'cmd;TurnLeft':(0,0,0,1),
    'cmd;TurnRight':(0,0,0,-1),
    'cmd;Backward':(-1,0,0,0),
    'cmd;Stop':(0,0,0,0)
}

addr = ''
port = 0
cws = None
scenario = ''

# 音声案内に関するコマンド
# 紹介文は以下のコマンドで実行 ["V_Self", "-> 登録済みの自己紹介プログラムを実行"]
V_cmdlist = [
    ['V_Booth1', 'AVITAのブースは、万博プロデューサー石黒浩さんのプログラムの1つです。アバター接客サービスを活用してアバターに場所を案内してもらいアバターキャラを探索体験できます。会場内のアバターを全員見つけると、いいことがあるかもしれません。'],
    ['V_ToiletM', '男性用トイレは１階西側通路を進んで左側にあります。大きな階段の左側を進んで下さい。'],
    ['V_ToiletW', '女性用トイレは１階東側通路を進んで右側にあります。展示エリアを抜けてまっすぐ進んで下さい。'],
    ['V_Staff', 'すみません、お答えが難しい質問です。黄色かピンク色のジャンバーを着たスタッフにお尋ねください。'],
    ['V_Space', 'すみませんが、通りたいので道をあけていただけないでしょうか。'],
]

# Teleco移動 / ジェスチャに関するコマンド
M_cmdlist = [
    'M_WestFar',
    'M_West',
    'M_Center',

    'M_BodyLeft',
    'M_BodyFront',
    'M_BodyRight',
    'M_LeftHand',
    'M_BothHand',
    'M_RightHand',
    'M_HeadShake',
    'M_Bow',
    'M_Run'
]

jsonCommands = [
    [   # no.0 - 自己紹介
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"こんにちは","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1500',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 750',
        {"@class":"commu.message.SayInfo","label":"say","text":"私は、移動型アバターの、テレコです","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1000',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 3000',
        {"@class":"commu.message.SayInfo","label":"say","text":"顔が有機ELディスプレイでできていて、静かに、自由に、動き回ることができるよ","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,3,4],"angles":[20,-50,0,50],"speeds":[20,50,50,50],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,5],"angles":[-10,10],"speeds":[20,20],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,5],"angles":[20,-10],"speeds":[20,20],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,5],"angles":[-10,10],"speeds":[20,20],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,5],"angles":[20,-10],"speeds":[20,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,4,5],"angles":[0,-50,0],"speeds":[20,50,20],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1000',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["-800","100","100"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_iris_position","x":-100,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_background_color","color":"#85a7d4","step":40,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_face","iris_number":3,"mask_number":3,"cheek_number":0,"eye_brow":0,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1000',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.SayInfo","label":"say","text":"こんなふうに、キャラクターを自由にかえられるよ","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 600',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveInfo","label":"move","joint":2,"angle":0,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveInfo","label":"move","joint":4,"angle":0,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1000',
        {"@class":"commu.message.MoveInfo","label":"move","joint":2,"angle":-90,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveInfo","label":"move","joint":4,"angle":-90,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1000',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1000',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["-800","100","100"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_iris_position","x":-100,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_background_color","color":"#b9c42f","step":40,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_face","iris_number":1,"mask_number":2,"cheek_number":1,"eye_brow":2,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 250',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room"},
        {"@class":"commu.message.SayInfo","label":"say","text":"そして、素早く、静かに、目を動かすこともできます","voice":"taichi","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 250',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveInfo","label":"move","joint":4,"angle":-200,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveInfo","label":"move","joint":2,"angle":-200,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveInfo","label":"move","joint":0,"angle":-100,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveInfo","label":"move","joint":6,"angle":200,"speed":300,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_iris_position","x":-100,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_iris_position","x":100,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_iris_position","x":100,"y":100,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_iris_position","x":100,"y":-100,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_iris_position","x":-100,"y":-100,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_iris_position","x":-100,"y":100,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_iris_position","x":-20,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveInfo","label":"move","joint":0,"angle":0,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveInfo","label":"move","joint":6,"angle":0,"speed":300,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveInfo","label":"move","joint":4,"angle":-90,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveInfo","label":"move","joint":2,"angle":-90,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"upper_flag\",\"desire_state\":0,\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"@class":"commu.message.MoveInfo","label":"move","joint":4,"angle":-20,"speed":50,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveInfo","label":"move","joint":2,"angle":-20,"speed":50,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["800","100","100"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_iris_position","x":-100,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',
        {"label":"faceCommand","commandFace":"change_background_color","color":"#B7A8CC","step":40,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_face","iris_number":2,"mask_number":1,"cheek_number":2,"eye_brow":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1000',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveInfo","label":"move","joint":4,"angle":-90,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveInfo","label":"move","joint":2,"angle":-90,"speed":100,"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.SayInfo","label":"say","text":"それに、くび","voice":"anzu","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 300',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[-30],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[30],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[-30],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[30],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[0],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"@class":"commu.message.SayInfo","label":"say","text":"うで、","voice":"anzu","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"banzai","data":"0.0\tP\t0.0\t70\t4\t40\t2\t40\t-1\n2.0\tP\t0.0\t70\t4\t-40\t2\t-40\t-1\n2.0\tP\t0.0\t70\t4\t40\t2\t40\t-1\n2.0\tP\t0.0\t70\t4\t-90\t2\t-90\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1000',
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"upper_flag\",\"desire_state\":1,\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"talking\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"start\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"@class":"commu.message.SayInfo","label":"say","text":"体の上下の動きを組み合わせて、多様な表現ができます","voice":"anzu","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 3000',
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"no_talking\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"start\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        '/wait 3000',
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"talking\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"start\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},'/wait 200',
        {"label":"faceCommand","commandFace":"change_face_emotion","emotion":"happy","mouth_emotion":"happy","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"happy\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"@class":"commu.message.SayInfo","label":"say","text":"うれしいときには、こんなふうに体全体でそれを表現できるよ","voice":"reina","speed":1.15,"volume":1,"pitch":1.1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"start\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},'/wait 6000',
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"stop\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        '/wait 3000',
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"no_talking\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"start\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},'/wait 500',
        {"label":"faceCommand","commandFace":"change_face_emotion","emotion":"sad","mouth_emotion":"happy","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"sad\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"@class":"commu.message.SayInfo","label":"say","text":"悲しいときにも、こんなふうに体全体でそれを表現できるよ","voice":"reina","speed":0.8,"volume":1,"pitch":0.85,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"start\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},'/wait 6000',
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"stop\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        '/wait 3000',
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"stop\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"@class":"commu.message.SayInfo","label":"say","text":"これで、テレコの説明をおわります。ありがとうございました","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 5000',
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 5000',
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"no_talking\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"stop\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"label": "clearFace", "id": "", "topic": "command", "client": 0, "room": "", "commu": 0},
        {"label": "faceCommand", "commandFace": "init_face", "id": "", "topic": "command", "client": 0, "room": "", "commu": 0},
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"clearFace","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,7],"angles":[75,-10,-18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"change_state","status":"stop","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[5,3,4,2],"angles":[0,0,-90,-90],"speeds":[50,50,50,50],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # no.1 - ブース2
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1500',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 750',
        {"label":"faceCommand","commandFace":"change_iris_position","x":75,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[4,5,7],"angles":[75,10,18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"label":"faceCommand","commandFace":"change_iris_position","x":0,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"アヴィータのブースは、万博プロデューサー石黒浩さんのプログラムの１つです。アバター接客サービスを活用してアバターに場所を案内してもらいアバターキャラを、探索体験できます。会場内のアバターを全員見つけると、いいことがあるかもしれません！","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 12000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # no.2 - 男子トイレ
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"場所の案内だね。任せてよ!","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 2000',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 750',
        {"label":"faceCommand","commandFace":"change_iris_position","x":-75,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,7],"angles":[75,-10,-18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"label":"faceCommand","commandFace":"change_iris_position","x":0,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"男性用トイレは１階西側通路を進んで左側にあります。大きな階段の左側を進んで下さい。","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 4000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # no.3 - 女性用トイレ
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"場所の案内だね。任せてよ!","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 2000',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 750',
        {"label":"faceCommand","commandFace":"change_iris_position","x":-75,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,7],"angles":[75,-10,-18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"label":"faceCommand","commandFace":"change_iris_position","x":0,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"女性用トイレは１階東側通路を進んで右側にあります。展示エリアを抜けてまっすぐ進んで下さい。","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 4000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # no.4 - すみません1
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"すみません、お答えが難しい質問です。弊社のスタッフにお尋ねください。","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 2500',
    ],
    [
        # no.5 - すみません2
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"すみませんが、通りたいので道をあけていただけないでしょうか。","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 3000',
    ],
    [
        ### no.6 - Short1
        {"label" :"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"ようこそスタートアップサイドへ！","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 800',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5],"angles":[75,-10,75,10],"speeds":[70,50,70,50],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,6,7],"angles":[-90,0,-90,0,15,0],"speeds":[50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500'
    ],
    [
        # no.7 - Short2
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"こんにちは、私の名前は、テレコです。この建物の中を案内できるよ！","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 2000',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 750',
        {"label":"faceCommand","commandFace":"change_iris_position","x":-75,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,7],"angles":[75,-10,-18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"label":"faceCommand","commandFace":"change_iris_position","x":0,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        '/wait 1000',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # no.8 - Short3
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"すみません、聞こえなかったのでもう一度話してくれませんか？","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 2000',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 750',
        {"label":"faceCommand","commandFace":"change_iris_position","x":-75,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"stop\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"label":"faceCommand","commandFace":"change_iris_position","x":0,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        '/wait 1000',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # no.9 - Short4
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"ばいばーい！またきてね！","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 800',
        {"label":"faceCommand","commandFace":"change_face_emotion","emotion":"happy","mouth_emotion":"happy","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"happy\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        '/wait 800',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5],"angles":[75,-10,75,10],"speeds":[70,50,70,50],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,6,7],"angles":[-90,0,-90,0,15,0],"speeds":[50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"no_talking\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"stop\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"label": "clearFace", "id": "", "topic": "command", "client": 0, "room": "", "commu": 0},
        {"label": "faceCommand", "commandFace": "init_face", "id": "", "topic": "command", "client": 0, "room": "", "commu": 0}
    ],
    [
        # no.10 - Short5　おこさま目線
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_face_emotion","emotion":"happy","mouth_emotion":"happy","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"happy\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"@class":"commu.message.SayInfo","label":"say","text":"今日は来てくれてありがとう！何か知りたいことはあるかな？ぜひ、話しかけてね！","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 400',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,3,5,6],"angles":[-15,-35,35,-20],"speeds":[10,10,10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[3,5],"angles":[0,0],"speeds":[10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[3,5],"angles":[-35,35],"speeds":[10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[3,5],"angles":[0,0],"speeds":[10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[3,5],"angles":[-35,35],"speeds":[10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[3,5],"angles":[0,0],"speeds":[10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[3,5],"angles":[-35,35],"speeds":[10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[3,5],"angles":[0,0],"speeds":[10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_emotion\",\"emotion\":\"no_talking\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"stop\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"label": "clearFace", "id": "", "topic": "command", "client": 0, "room": "", "commu": 0},
        {"label": "faceCommand", "commandFace": "init_face", "id": "", "topic": "command", "client": 0, "room": "", "commu": 0},
    ],
    [
        ### no.11 - 左に向く 胴体ヨーを90度回転
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1],"angles":[-90],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1000',
    ],
    [
        # no.12 - 正面に向く
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1000'
    ],
    [
        # no.13 - 右に向く 胴体ヨーを-90度回転
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1],"angles":[90],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1000'
    ],
    [
        # no.14 - 左手を上げる
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,7],"angles":[75,-10,-18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,6,7],"angles":[-90,0,-90,0,15,0],"speeds":[50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500'
    ],
    [
        # no.15 - 両手を上げる
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,7],"angles":[75,-10,75,10,-18],"speeds":[70,50,70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,6,7],"angles":[-90,0,-90,0,15,0],"speeds":[50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500'
    ],
    [
        # no.16 - 右手を上げる
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[4,5,7],"angles":[75,10,18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,6,7],"angles":[-90,0,-90,0,15,0],"speeds":[50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500'
    ],
    [
        # no. 17 - 首を振る
        # 両手を降ろす
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,4],"angles":[0,-90,-90],"speeds":[20,75,75],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 200',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[-30],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_iris_position","x":-75,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[30],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_iris_position","x":75,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[-30],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_iris_position","x":0,"y":0,"framestoachieve":2,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[30],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[7],"angles":[0],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 300'
    ],
    [
        # no.18 - おじぎ
        {"label":"faceCommand","commandFace":"change_face_emotion","emotion":"no_talking","mouth_emotion":"happy","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":11,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"stop\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 2500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_face_emotion","emotion":"happy","mouth_emotion":"happy","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"ip":jetsonIP,"port":"11925","label":"externalCommand","data":"{\"command\":\"change_state\",\"status\":\"moving\",\"id\":\"\",\"topic\":\"command\",\"client\":0,\"room\":\"\",\"commu\":0}"},
    ],
    [
        # no.19 - 走る （かがむ -> 右手を前に、左手を後ろに -> 右手を後ろに、左手を前に）
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[4,5,7],"angles":[75,10,18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.SayInfo","label":"say","text":"移動しまーーす。","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        
        # 初期姿勢 かがめはしない
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,2,3,4,5,6,7],"angles":[-15,-90,-10,-90,10,20,0],"speeds":[10,50,10,50,10,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',

        # テ 左手を前に、右手を後ろに
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,4],"angles":[10,-45,-135],"speeds":[20,75,75],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',

        # ク　左手を後ろに、右手を前に
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,4],"angles":[-10,-135,-45],"speeds":[20,75,75],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',

        # テ 左手を前に、右手を後ろに
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,4],"angles":[10,-45,-135],"speeds":[20,75,75],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',

        # ク　左手を後ろに、右手を前に
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,4],"angles":[-10,-135,-45],"speeds":[20,75,75],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 500',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6],"angles":[-15,0,-90,-10,-90,10,20],"speeds":[10,10,50,10,50,10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
    ],
    # 以下、走る動作を3つに分割
    # no.20 ① 掛け声のみ
    [
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[4,5,7],"angles":[75,10,18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.SayInfo","label":"say","text":"移動しまーーす。","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        
        # 初期姿勢 かがめはしない
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,2,3,4,5,6,7],"angles":[-15,-90,-10,-90,10,20,0],"speeds":[10,50,10,50,10,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
    ],
    # no.21 ② テクテク
    [
        # テ 左手を前に、右手を後ろに
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,4],"angles":[10,-45,-135],"speeds":[20,75,75],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 600',

        # ク　左手を後ろに、右手を前に
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,4],"angles":[-10,-135,-45],"speeds":[20,75,75],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 600',

        # テ 左手を前に、右手を後ろに
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,4],"angles":[10,-45,-135],"speeds":[20,75,75],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 600',

        # ク　左手を後ろに、右手を前に
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1,2,4],"angles":[-10,-135,-45],"speeds":[20,75,75],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 600',
    ],
    # no.22 ③ ついたよ
    [
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6],"angles":[-15,0,-90,-10,-90,10,20],"speeds":[10,10,50,10,50,10,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,7],"angles":[75,-10,75,10,-18],"speeds":[70,50,70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"とうちゃくぅー！","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,6,7],"angles":[-90,0,-90,0,15,0],"speeds":[50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500'
    ],
    # no.23 ④ えっほえっほ
    [
        {"@class":"commu.message.SayInfo","label":"say","text":"動きます。ご注意ください。","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
    ],
]

def goal_pose(pose): 
    goal_pose = MoveBaseGoal()
    goal_pose.target_pose.header.frame_id = 'map'
    goal_pose.target_pose.pose.position.x = pose[0][0]
    goal_pose.target_pose.pose.position.y = pose[0][1]
    goal_pose.target_pose.pose.position.z = pose[0][2]
    goal_pose.target_pose.pose.orientation.x = pose[1][0]
    goal_pose.target_pose.pose.orientation.y = pose[1][1]
    goal_pose.target_pose.pose.orientation.z = pose[1][2]
    goal_pose.target_pose.pose.orientation.w = pose[1][3]

    return goal_pose


def sendJsonCommand(ws, index):
    commands = jsonCommands[index]
    for msg in commands:
        print(msg)
        if(type(msg) is dict):
            ws.send(json.dumps(msg))
        else:
            cols = msg.split('/wait')
            millisec = int(cols[1])
            time.sleep(millisec / 1000.0)


# j -> for handai system
def on_message_j(ws, message):
    print('M:', message)

def on_error_j(ws, error):
    print('E:', error)

def on_close_j(ws):
    print("Closing")

def on_open_j(ws):
    print("openning")
    # sendJsonCommand(ws, 6)


# no j -> for capf
def on_error(ws, error):
    print('Ex:', error)

def on_close(ws):
    print("Closing")

def on_open(ws):
    print("openning")


def on_message(ws, message):
    global cws
    global addr
    global port
    global scenario
    scenario = ''

    if message == 'something' : return
    print('M:', message, addr, port, cws)
    sota = (addr, port)
    cmd = message
    # print(cmd)
    header = message[:1]

    # 音声案内コマンド
    if header == "V" :
        if cmd == "V_Self" :
            sendJsonCommand(cws, 0)
        else :
            num_i = 0
            while cmd != V_cmdlist[num_i][0] :
                num_i += 1
            scenario = V_cmdlist[num_i][1]
            sendJsonCommand(cws, num_i + 1)
            print ('\033[34m' + V_cmdlist[num_i][0] + ' 音声案内のコマンドを受け取ったよ。場所の案内やブースの紹介文を発話するね: \n' + scenario + '\033[0m')


    # ショート動作コマンド
    if header == "H" :
        if cmd == "H_short1" :
            sendJsonCommand(cws, 6)
            print ('\033[34m' + ' 短い音声案内のコマンドを受け取ったよ。短く挨拶するね: \n' + '\033[0m')
        if cmd == "H_short2" :
            sendJsonCommand(cws, 7)
            print ('\033[34m' + '短い音声案内のコマンドを受け取ったよ。短く挨拶するね: \n' + '\033[0m')
        if cmd == "H_short3" :
            sendJsonCommand(cws, 8)
            print ('\033[34m' + '短い音声案内のコマンドを受け取ったよ。短く挨拶するね: \n' + '\033[0m')
        if cmd == "H_short4" :
            sendJsonCommand(cws, 9)
            print ('\033[34m' + '短い音声案内のコマンドを受け取ったよ。短く挨拶するね: \n' + '\033[0m')
        if cmd == "H_short5" :
            sendJsonCommand(cws, 10)
            print ('\033[34m' + '短い音声案内のコマンドを受け取ったよ。短く挨拶するね: \n' + '\033[0m')


    # 動作コマンド
    if header == "M" :
        print ('\033[32m' + '動作コマンド ' + cmd + ' を実行するね' + '\033[0m')
        if cmd == "M_BodyLeft" :
            sendJsonCommand(cws, 11)
        if cmd == "M_BodyFront" :
            sendJsonCommand(cws, 12)
        if cmd == "M_BodyRight" :
            sendJsonCommand(cws, 13)
        if cmd == "M_LeftHand" :
            sendJsonCommand(cws, 14)
        if cmd == "M_BothHand" :
            sendJsonCommand(cws, 15)
        if cmd == "M_RightHand" :
            sendJsonCommand(cws, 16)
        if cmd == "M_HeadShake" :
            sendJsonCommand(cws, 17)
        if cmd == "M_Bow" :
            sendJsonCommand(cws, 18)
        if cmd == "M_Run" :
            sendJsonCommand(cws, 19)


    # N_1 ~ N_5
    if header == "N" :
        client.cancel_goal()  # 実行中のnavigationを中断するリクエスト
        point = cmd[2]   # コマンドの3文字目を取得してインデックス番号として変数pointに代入

        print ('\033[32m' + '周りの人に移動開始を伝えるね' + '\033[0m')
        sendJsonCommand(cws, 20)

        try:
            goal = goal_pose(waypoints[int(point)-1])
            client.send_goal(goal)
            print ('\033[32m' + point + ' まで自律移動を開始するね。' + '\033[0m')
            nav_time_init = time.time()

            while not rospy.is_shutdown():
                nav_time = time.time()
                status = client.get_state()  #ゴールの状態を数値で取得（PREEMPTED=2, SUCCEEDED=3, ABORTED=4）
                print(f"[Result] Status: {status}")   #ゴールの状態を表示
                
                ## 目的地に到着した場合:
                if status == 3:
                    print ('\033[32m' + point + ' に到着したよ。' + '\033[0m')
                    time.sleep(1.0)
                    sendJsonCommand(cws, 22)
                    break
                ## 1分半以上経っても目的地に辿り着かない場合:
                elif nav_time - nav_time_init >= 90:
                    print ('\033[32m' + '迷っちゃったから、自律移動を停止するよ。' + '\033[0m')
                    time.sleep(1.0)
                    sendJsonCommand(cws, 22)
                    break
                elif status == 1:
                    
                    time.sleep(1.0)
                    rand = random.random()
                    if rand > 0.2:
                        sendJsonCommand(cws, 21)      # 走るモーション
                        if rand > 0.5:
                            sendJsonCommand(cws, 23)  # アナウンス
                    else:
                        sendJsonCommand(cws, 17)      # 首振りモーション

        except rospy.ROSInterruptException:
            rospy.loginfo("Navigation test finished.")

    else :
        if cmd == "cmd;Forward" or cmd == "cmd;TurnLeft" or cmd == "cmd;TurnRight" or cmd == "cmd;Backward" or cmd == "cmd;Stop":
            print ('\033[33m' + cmd + ' ... マニュアルモードで移動するよ。' + '\033[0m')
            p=rospy.Publisher('rover_twist',Twist, queue_size=10)
            rate = rospy.Rate(10)

            x = moveBindings[cmd][0]
            y = moveBindings[cmd][1]
            z = moveBindings[cmd][2]
            th = moveBindings[cmd][3]
            
            t = Twist()
            t.linear.x = x * 0.1
            t.linear.y = y * 0.1
            t.linear.z = z * 0.1
            t.angular.x = 0
            t.angular.y = 0
            t.angular.z = th * 0.2
            
            for i in range(0, 5) :
                p.publish(t)
                rate.sleep()
        
        # print(cmd)
        if cmd == "cmd;scenario;self_intro" :
            sendJsonCommand(cws, 0)

if __name__ == '__main__':
    print(ros_msg)
    #global cws
    #global addr
    #global port

    if (len(sys.argv) != 9):
        print("Usage: {} <login url> <id> <passwd> <websocket url> <jetson ip> <jetson port> <handaisys ip> <handaisys port>".format(sys.argv[0]))
        sys.exit(1)

    login_url = sys.argv[1]
    sid = sys.argv[2]
    passwd = sys.argv[3]

    websockurl = sys.argv[4]
    addr = sys.argv[5]
    port = int(sys.argv[6])
    handaiip = (sys.argv[7], int(sys.argv[8]))
    websocket.enableTrace(True)

    print('teleco-H =', handaiip)
    cws = websocket.WebSocketApp("ws://%s:%d/command" %( handaiip[0], handaiip[1]),
                              on_message = on_message_j,
                              on_error = on_error_j,
                              on_close = on_close_j)
    #cws.on_open = on_open_j
    cwst = threading.Thread(target=cws.run_forever)
    cwst.daemon = True
    cwst.start()

    payload = {"name" : sid, "password" : passwd}
    r = requests.post(login_url, params = payload)
    authorisation = json.loads(r.text)["authorisation"]
    token = authorisation["token"]
    ws = websocket.WebSocketApp(websockurl + "?token=" + token,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    wst = threading.Thread(target = ws.run_forever)
    wst.daemon = True
    wst.start()
    try:
        while not rospy.is_shutdown():
            time.sleep(1.0)
    except KeyboardInterrupt:
        print('Ctrl-C を受け取りました。プログラムを終了します,,,,,,')
        sys.exit(1)