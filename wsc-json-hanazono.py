# coding: utf-8

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

jetsonIP = "192.168.100.201"


rospy.init_node('capf_navigation') #ノードの初期化
# demo_Hanazono.pyでは emotional_walk ノードを作成します

client = actionlib.SimpleActionClient('move_base', MoveBaseAction)    #サーバ名，型ともに利用するサーバと一致させる
client.wait_for_server()    #サーバーの応答を待つ
# listener.waitForTransform("map", "base_link", rospy.Time(), rospy.Duration(2.0))
ros_msg = "ROS:: wait_for_server ...."

nav_dict = {
    # 西側通路
    'M_WestFar':(3.08, 3.88, 0.0, 0.0, 0.0, 0.0, 1.0),
    # 西ブース
    'M_West':(3.02, 7.13, 0.0, 0.0, 0.0, 0.0, 1.0),
    # 中央ブース
    'M_Center':(3.02, 13.37, 0.0, 0.0, 0.0, 0.0, 1.0),
    # 東ブース
    'M_East':(0.15, 24.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    # 東側通路
    'M_EastFar':(-3.72, -5.03, 0.0, 0.0, 0.0, 0.71, 0.71),
    # 待機場所
    'M_Waiting':(-0.15, -0.82, 0.0, 0.0, 0.0, 1.0, 0.0),
}

# hanazonoデモでは不使用
moveBindings = {
    'cmd;Forward':(1,0,0,0),
    'cmd;TurnLeft':(0,0,0,1),
    'cmd;TurnRight':(0,0,0,-1),
    'cmd;Backward':(-1,0,0,0),
}

addr = ''
port = 0
cws = None
scenario = ''

# 音声案内に関するコマンド
# 紹介文は以下のコマンドで実行 ["V_Self", "-> 登録済みの自己紹介プログラムを実行"]
V_cmdlist = [
    ['V_Booth1', 'ティフォンのブースでは、タロットのストーリーを先端技術を駆使したVRで体験することで、より豊かにタロットの意味合いを理解して新感覚のタロット占いを楽しんでいただきます。'],
    ['V_Booth2', 'AVITAのブースは、万博プロデューサー石黒浩さんのプログラムの1つです。アバター接客サービスを活用してアバターに場所を案内してもらいアバターキャラを探索体験できます。会場内のアバターを全員見つけると、いいことがあるかもしれません。'],
    ['V_Booth3', 'デロイトトーマツとDreamOnのブースでは、VRを活用して空飛ぶクルマの搭乗手続きから機内での過ごし方、目的地到着までのアクティビティを体験し、ミライにおける空飛ぶクルマのポテンシャルを感じていただくことができます。'],
    ['V_Booth4', 'MASCのブースでは、実際に飛ぶことができる空飛ぶクルマの実機を展示しています。実機に乗って記念撮影もできます。'],
    ['V_Booth5', 'プレースホルダのブースでは、VR技術を使ったインクの出ないデジタル落書きや、砂の形状にあわせて本物の山や海が出現する未来の砂場体験ができます。小さなお子さんの体験にぴったりです。'],
    ['V_Booth6', 'アシストモーションのブースでは、ロボットの展示と、歩行アシストロボットの体験ができます。人にやさしい、「着る」ロボットの実現を目指しています。'],
    ['V_Booth7', 'ドローンプラスのブースでは、ドローンの展示と、実際にドローンの操縦体験ができます。'],
    ['V_Booth8', 'スカイドライブ社の最新機体のパネルの展示や、映像展示を行っています。'],
    ['V_Booth9', '国立研究開発法人 情報通信研究機構のブースでは、高齢者の健康状態などを対話で把握するAIシステムを展示・体験できます。Webのデータを活用した雑談で高齢者のコミュニケーション不足の抑制を目指しています。'],
    ['V_Booth10', 'ミズノのブースでは、歩くチカラを１分で測定します。歩行能力を把握して健康状態をチェックしましょう。'],
    ['V_Booth11', 'マイボトルを持っていれば、自由に水を飲んでいただける、ダイオーズジャパンが提供するウォーターサーバーです。2階・3階にもサーバーを設置しています。'],

    ['V_Booth12', '西側の大きい階段から2階へ上がると、HADOやロジリシティのどこでもバンジーなど、VR技術を駆使したコンテンツが楽しめるデジタルエンターテイメントゾーンが広がっています。'],
    ['V_Booth13', '入口両脇の階段から2階へ上がると、モビリティ型ロボットの体験ができるロジリシティのブースと、ユニエイムが提供するTOKYO OUTLET WEEK in HANAZONO EXPOのブースがあります。'],
    ['V_Booth14', '3階へ上がると、スパーキークリエイトの鳥型ドローン操作や、エディックスのハンドランチグライダー、夢洲機構所属企業集合団体のストライダー体験があります。'],

    ['V_ToiletM', '男性用トイレは１階西側通路を進んで左側にあります。大きな階段の左側を進んで下さい。'],
    ['V_ToiletW', '女性用トイレは１階東側通路を進んで右側にあります。展示エリアを抜けてまっすぐ進んで下さい。'],
    ['V_Staff', 'すみません、お答えが難しい質問です。黄色かピンク色のジャンバーを着たスタッフにお尋ねください。'],
    ['V_Space', 'すみませんが、通りたいので道をあけていただけないでしょうか。']
]

# Teleco移動 / ジェスチャに関するコマンド
M_cmdlist = [
    'M_WestFar',
    'M_West',
    'M_Center',
    'M_East',
    'M_EastFar',
    'M_Waiting',

    'M_BodyLeft',
    'M_BodyFront',
    'M_BodyRight',
    'M_LeftHand',
    'M_BothHand',
    'M_RightHand',
    'M_HeadShake',
    'M_Bow'
]

jsonCommands = [
    [
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"こんにちは","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1500',
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 750',
        {"@class":"commu.message.SayInfo","label":"say","text":"私は移動型CAのテレコです","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 500',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 1000',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":10,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 200',
        {"label":"faceCommand","commandFace":"change_eye_lid_position","eyelidposition":0,"framestoachieve":1,"eyes":"both","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 3000',
        {"@class":"commu.message.SayInfo","label":"say","text":"顔が有機ELディスプレイでできているのが大きな特徴です","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"こんなふうに、キャラクターを自由にかえられるよ","voice":"maki","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 600',
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
        {"@class":"commu.message.SayInfo","label":"say","text":"これで、テレコの説明をおわります。ありがとうございました","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},'/wait 5000',
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
        # ブース1
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"ティフォンのブースでは、タロットのストーリーを先端技術を駆使したVRで体験することで、より豊かにタロットの意味合いを理解して新感覚のタロット占いを楽しんでいただきます。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 2000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース2
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"アヴィータのブースは、万博プロデューサー石黒浩さんのプログラムの１つです。アバター接客サービスを活用してアバターに場所を案内してもらいアバターキャラを、探索体験できます。会場内のアバターを全員見つけると、いいことがあるかもしれません！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 12000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース3
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"デロイトトーマツとドリームオンのブースでは、VRを活用して空飛ぶクルマの搭乗手続きから機内での過ごし方、目的地到着までのアクティビティを体験し、ミライにおける空飛ぶクルマのポテンシャルを感じていただくことができます。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 10000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース4
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"マスク、のブースでは、実際に飛ぶことができる空飛ぶクルマの実機を展示しています。実機に乗って記念撮影もできます。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 4000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース5
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"プレースホルダのブースでは、VR技術を使ったインクの出ないデジタル落書きや、砂の形状にあわせて本物の山や海が出現する未来の砂場体験ができます。小さなお子さんの体験にぴったりです。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 6000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース6
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"アシストモーションのブースでは、ロボットの展示と、歩行アシストロボットの体験ができます。人にやさしい、「着る」ロボットの実現を目指しています。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 6000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース7
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"ドローンプラスのブースでは、ドローンの展示と、実際にドローンの操縦体験ができます。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 4000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース8
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"このブースでは、スカイドライブ社の最新機体のパネルの展示や、映像展示を行っています。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 4000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース9
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"国立研究開発法人 情報通信研究機構のブースでは、高齢者の健康状態などを対話で把握するAIシステムを展示、体験できます。Webのデータを活用した雑談で高齢者のコミュニケーション不足の抑制を目指しています。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 10000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース10
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"ミズノのブースでは、歩くチカラを１分で測定します。歩行能力を把握して健康状態をチェックしましょう。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 4000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース11
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"それじゃあブースを紹介するよ！","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"マイボトルを持っていれば、自由に水を飲んでいただける、ダイオーズジャパンが提供するウォーターサーバーです。2階・3階にもサーバーを設置しています。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 5000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
        [
        # ブース12
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"場所の案内だね。任せてよ!","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"西側の大きい階段から2階へ上がると、HADOやロジリシティのどこでもバンジーなど、VR技術を駆使したコンテンツが楽しめるデジタルエンターテイメントゾーンが広がっています。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 10000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース13
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"場所の案内だね。任せてよ!","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"入口両脇の階段から2階へ上がると、モビリティ型ロボットの体験ができるロジリシティのブースと、ユニエイムが提供する東京アウトレット ウィークイン花園エキスポのブースがあります。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 10000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # ブース14
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"場所の案内だね。任せてよ!","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"3階へ上がると、スパーキークリエイトの鳥型ドローン操作や、エディックスのハンドランチグライダー、夢洲機構所属企業集合団体のストライダー体験があります。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 8000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # 男子トイレ
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"場所の案内だね。任せてよ!","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"男性用トイレは１階西側通路を進んで左側にあります。大きな階段の左側を進んで下さい。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 4000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # 女性用トイレ
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"場所の案内だね。任せてよ!","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
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
        {"@class":"commu.message.SayInfo","label":"say","text":"女性用トイレは１階東側通路を進んで右側にあります。展示エリアを抜けてまっすぐ進んで下さい。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},

        '/wait 4000',

        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0}
    ],
    [
        # すみません1
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"すみません、お答えが難しい質問です。黄色かピンク色のジャンバーを着たスタッフにお尋ねください。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 2500',
    ],
    [
        # すみません2
        {"label":"faceCommand","commandFace":"init_face","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.LookInfo","label":"look","name":"manual","pos":["0","400","300"],"cr":[0.5,0.5,0.5,0.5,0.5,0.5],"speed":[30,30,30,30,100,100,100],"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":0,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.GestureInfo","label":"gesture","name":"ojigi","data":"\n0.5\tP\t0.0\t20\t0\t-15\t6\t-20.0\t-1\n0.0\tP\t0.2\t20\t3\t-2\t5\t2\t-1\n\n1.0\tP\t0.0\t20\t0\t0\t6\t0\t-1\n0.0\tP\t0.2\t20\t3\t-5\t5\t5\t-1\n\n1.0\tt\n","relative":"false","id":"","topic":"command","client":0,"room":"room","commu":0},
        {"command":"upper_flag","desire_state":1,"id":"","topic":"command","client":0,"room":"room","commu":0},
        {"@class":"commu.message.SayInfo","label":"say","text":"すみませんが、通りたいので道をあけていただけないでしょうか。","voice":"reina","speed":1,"volume":1,"pitch":1,"pause":800,"device":"default","id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 3000',
    ],
    [
        # 左に向く 胴体ヨーを90度回転
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1],"angles":[-90],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1000',
    ],
    [
        # 正面に向く
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[0,1,2,3,4,5,6,7],"angles":[20,0,-90,0,-90,0,15,0],"speeds":[10,20,50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1000'
    ],
    [
        # 右に向く 胴体ヨーを-90度回転
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[1],"angles":[90],"speeds":[20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1000'
    ],
    [
        # 左手を上げる
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,7],"angles":[75,-10,-18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,6,7],"angles":[-90,0,-90,0,15,0],"speeds":[50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500'
    ],
    [
        # 両手を上げる
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,7],"angles":[75,-10,75,10,-18],"speeds":[70,50,70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,6,7],"angles":[-90,0,-90,0,15,0],"speeds":[50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500'
    ],
    [
        # 右手を上げる
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[4,5,7],"angles":[75,10,18],"speeds":[70,50,10],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500',
        {"@class":"commu.message.MoveMultiInfo","label":"move_multi","joints":[2,3,4,5,6,7],"angles":[-90,0,-90,0,15,0],"speeds":[50,50,50,50,10,20],"id":"","topic":"command","client":0,"room":"room","commu":0},
        '/wait 1500'
    ],
    [
        # 首を振る
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
        # おじぎ
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
]

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

    # 音声案内コマンド 18 items   先頭 11items はブース紹介用 -- 2022/10/28  -- 2022/10/28
    if header == "V" :
        if cmd == "V_Self" :
            sendJsonCommand(cws, 0)
        else :
            num_i = 0
            while cmd != V_cmdlist[num_i][0] :
                num_i += 1
            scenario = V_cmdlist[num_i][1]

            if num_i < 11 :
                sendJsonCommand(cws, num_i + 1)
                print ('\033[34m' + V_cmdlist[num_i][0] + ' 音声案内のコマンドを受け取ったよ。ブースの紹介文を発話するね: \n' + scenario + '\033[0m')
            else :
                sendJsonCommand(cws, num_i + 1)
                print ('\033[34m' + V_cmdlist[num_i][0] + ' 音声案内のコマンドを受け取ったよ。場所の案内を開始するね: \n' + scenario + '\033[0m')

    # 動作コマンド 14 items   先頭 6items はナビゲーション用 -- 2022/10/28
    if header == "M" :
        num_j = 0
        while cmd != M_cmdlist[num_j] :
            num_j += 1

        if num_j < 6 :
            client.cancel_goal()    #実行中のnavigationを中断するリクエスト
            try:
                goal_pose = MoveBaseGoal()
                goal_pose.target_pose.header.frame_id = 'map'
                goal_pose.target_pose.pose.position.x = nav_dict[cmd][0]
                goal_pose.target_pose.pose.position.y = nav_dict[cmd][1]
                goal_pose.target_pose.pose.position.z = nav_dict[cmd][2]
                goal_pose.target_pose.pose.orientation.x = nav_dict[cmd][3]
                goal_pose.target_pose.pose.orientation.y = nav_dict[cmd][4]
                goal_pose.target_pose.pose.orientation.z = nav_dict[cmd][5]
                goal_pose.target_pose.pose.orientation.w = nav_dict[cmd][6]
                #clientとしてgoalをサーバーに送ると同時にfeedback_cb関数を呼び出す
                result = client.send_goal(goal_pose)
                print ('\033[32m' + M_cmdlist[num_j] + ' ... ナビゲーションを実行するね。' + '\033[0m')
                if result:
                    print(result)
                    rospy.loginfo("Goal execution done!")
            except rospy.ROSInterruptException:
                rospy.loginfo("Navigation test finished.")

        else :
            sendJsonCommand(cws, num_j + 13)
            print ('\033[32m' + '動作コマンド ' + M_cmdlist[num_j] + ' を実行するね' + '\033[0m')

    else :
        # print(cmd)
        if cmd == "cmd;scenario;self_intro" :
            sendJsonCommand(cws, 0)
        elif cmd == "cmd;scenario;pr_001" :
            sendJsonCommand(cws, 1)
        elif cmd == "cmd;scenario;pr_002" :
            sendJsonCommand(cws, 2)
        # 以下、tcp-clientによるTeleco-V側の操作
        # try :
        #     sota_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     sota_soc.connect(sota)
        #     sota_soc.send(cmd.encode('utf-8')) #(bytes(cmd))
        #     #cmd = st.readline()
        #     sota_soc.close()
        #     sota_soc = None
        # except :
        #     print('Teleco-Vとの通信に失敗しました :', datetime.now())


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

    print('handai =', handaiip)
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
        # while True :
            time.sleep(1.0)
    except KeyboardInterrupt:
        print('Ctrl-C を受け取りました。プログラムを終了します,,,,,,')
        sys.exit(1)