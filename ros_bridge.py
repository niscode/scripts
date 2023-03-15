#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float32
from geometry_msgs.msg import Twist, Point, Pose
from visualization_msgs.msg import Marker
import json

POS_X = POS_Y = POS_Z = ORI_Z = ORI_W = VOLTAGE = 0.0
MPOS_X = []
MPOS_Y = []
MORI_Z = []
MORI_W = []


def pose_callback(msg_pose):
    global POS_X, POS_Y, ORI_Z, ORI_W
    POS_X = msg_pose.position.x
    POS_Y = msg_pose.position.y
    ORI_Z = msg_pose.orientation.z
    ORI_W = msg_pose.orientation.w
    # print("[current x]   " + str(POS_X))
    # print("[current y]   " + str(POS_Y))
    # print("[current zth] " + str(ORI_W))
    # print("[current wth] " + str(ORI_W))


def point_callback(msg_point):
    global POS_Z
    POS_Z = msg_point.z
    # print("[current height] " + str(POS_Z))


def marker_callback(msg_marker):
    global MPOS_X, MPOS_Y, MORI_Z, MORI_W
    MPOS_X.append(msg_marker.pose.position.x)
    MPOS_Y.append(msg_marker.pose.position.y)
    MORI_Z.append(msg_marker.pose.orientation.z)
    MORI_W.append(msg_marker.pose.orientation.w)
    # print("[ ]" + str(msg_marker.id))


def voltage_callback(msg_voltage):
    global VOLTAGE
    VOLTAGE = msg_voltage.data


def spinOnce(sub, topic, type):
    rospy.wait_for_message(topic, type, timeout=None)
    sub.unregister();   # 1度だけ呼び出してからsubscriberを停止する


if __name__ == '__main__':
    rospy.init_node('ros_bridge')
    rate = rospy.Rate(10)

    # pub_pos = rospy.Publisher('/cylinder_pos', Point, queue_size=10)
    # pub = rospy.Publisher('rover_twist', Twist, queue_size=10)

    ## voltageをサブスクライブ
        # data: 27.7689990997
    sub_voltage = rospy.Subscriber("voltage", Float32, voltage_callback)

    ## Telecoの現在位置をサブスクライブ
        # position: 
        # x: -2.65817689896
        # y: -1.50309681892
        # z: 0.0
        # orientation: 
        # x: 0.0
        # y: 0.0
        # z: 0.652981090176
        # w: 0.757374211254
    sub_robotPose = rospy.Subscriber("robot_pose", Pose, pose_callback)

    ## シリンダーの高さをサブスクライブ
        # x: 0.0
        # y: 0.0
        # z: 1.0
    sub_cylinderPos = rospy.Subscriber("cylinder_pos", Point, point_callback)

    ## waypoint（目標地点）をサブスクライブ
        # id: 2
        # pose: 
        # position: 
        #     x: 0.7238894701
        #     y: 1.30770945549
        #     z: 0.0
        # orientation: 
        #     x: 0.0
        #     y: 0.0
        #     z: 0.829478281279
        #     w: 0.558538969891
        #  部分的に取得：ほんとはもっと長い
    sub_waypoint = rospy.Subscriber("waypoint", Marker, marker_callback)
    spinOnce(sub_waypoint, "waypoint", Marker)


    ## 辞書型に変換
    marker_dict = {
        "mpos_x": list(dict.fromkeys(MPOS_X)),  ## 配列から重複した要素を削除
        "mpos_y": list(dict.fromkeys(MPOS_Y)),  ## 配列から重複した要素を削除
        "mori_z": list(dict.fromkeys(MORI_Z)),  ## 配列から重複した要素を削除
        "mori_w": list(dict.fromkeys(MORI_W))   ## 配列から重複した要素を削除
    }
    # print("[marker dict] " + str(marker_dict))
    marker_json = json.dumps(marker_dict)
    print("[JSON MARKER-POS] " + str(marker_json))


    while not rospy.is_shutdown():
        sub_robotPose = rospy.Subscriber("robot_pose", Pose, pose_callback)
        sub_cylinderPos = rospy.Subscriber("cylinder_pos", Point, point_callback)
        sub_voltage = rospy.Subscriber("voltage", Float32, voltage_callback)
        pos_dict = {
            "voltage": VOLTAGE,
            "pos_x": POS_X,
            "pos_y": POS_Y,
            "pos_z": POS_Z,
            "ori_z": ORI_Z,
            "ori_w": ORI_W,
        }

        pos_json = json.dumps(pos_dict)
        print("[JSON TELECO-POS] " + str(pos_json))
        rospy.sleep(1.0)    # 1秒おきにTelecoの現在の姿勢を送信
        rate.sleep()