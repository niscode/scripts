from ws_utilze import *
import time

def global_status_defintion_outside(globalstatus):
    receive_global_status(globalstatus)

def body_movements(f0, energy, period, emotion, f0_com, eneragy_com, ws_commu, scale): 
    '''
    5, right shoulder roll
    3, left shoulder roll
    4, right shoulder pitch
    2, left shoulder pitch
    0, waist pitch
    6, head pitch
    7, head roll
    8: head yaw
    1, waist yaw
    '''

    if emotion == "happy":
        
        period_1 = period * 0.8
        period_2 = period * 0.15

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [-10, 10, -51, -51, 0, 10, 14, 0, 0], 
                        [5, 5, 70, 70, 8, 5, 5, 5, 20], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [45, 4, -51, 45, -15, 10, 14, 5, 13], [50, 50, 70, 70, 15, 5, 5, 5, 20], ws_commu)
        time.sleep(period_1)

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [-10, 10, -51, -51, 0, 10, 14, 0, 0], 
                        [5, 5, 70, 70, 8, 5, 5, 5, 20], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [-4, -45, 45, -51, 15, 10, 14, -5, -13], [50, 50, 70, 70, 15, 5, 5, 5, 20], ws_commu)
        time.sleep(period_1)

    elif emotion == "happy_skip":

        period_1 = period * 0.8
        period_2 = period * 0.15

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [-10, 10, -51, -51, 0, 10, 14, 0, 0], 
                        [5, 5, 70, 70, 8, 5, 5, 5, 20], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [45, 4, -51, 45, -15, 10, 14, 5, 13], [50, 50, 70, 70, 15, 5, 5, 5, 20], ws_commu)
        time.sleep(period_1)

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [-10, 10, -51, -51, 0, 10, 14, 0, 0], 
                        [5, 5, 70, 70, 8, 5, 5, 5, 20], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [-4, -45, 45, -51, 15, 10, 14, -5, -13], [50, 50, 70, 70, 15, 5, 5, 5, 20], ws_commu)
        time.sleep(period_1)


    elif emotion == "neutral":

        period_1 = period * 1.05
        period_2 = period * 0.

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [8, 10, -65, -65, 0, 0, 10, 0, 0], 
                        [50, 50, 70, 70, 15, 5, 5, 5, 20], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [-11, -12, 10, -65, 1, 0, 10, 1, 9], [50, 50, 70, 70, 15, 5, 5, 5, 20], ws_commu)
        time.sleep(period_1)

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [-10, -8, -65, -65, 0, 0, 10, 0, 0], 
                        [50, 50, 70, 70, 15, 5, 5, 5, 20], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [12, 11, -65, 10, -1, 0, 10, -1, -9], [50, 50, 70, 70, 15, 5, 5, 5, 20], ws_commu)
        time.sleep(period_1)


    elif emotion == "sad":

        period_1 = period * 0.95
        period_2 = period * 0.

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [20, 10, -76, -76, 0, -10, -10, 0, 0], 
                        [20, 20, 30, 30, 15, 5, 5, 5, 10], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [-13, -15, -16, -76, 11, -10, -10, 3, 9], [20, 20, 30, 30, 15, 5, 5, 5, 10], ws_commu)
        time.sleep(period_1)

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [-10, -20, -76, -76, 0, -10, -10, 0, 0], 
                        [20, 20, 30, 30, 15, 5, 5, 5, 10], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [14, 13, -76, -16, -5, -10, -10, -1, -11], [20, 20, 30, 30, 15, 5, 5, 5, 10], ws_commu)
        time.sleep(period_1)


    elif emotion == "angry":

        period_1 = period * 0.5
        period_2 = period * 0.
        period_3 = period_1
        period_4 = period_2

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [0, 0, -65, -65, 0, -10, 12, 0, 0], 
                        [50, 50, 90, 90, 15, 5, 5, 15, 20], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [47, -5, 25, -65, 1, -10, 12, 5, 13], [50, 50, 90, 90, 15, 5, 5, 15, 20], ws_commu)
        time.sleep(period_1)

        if period_2 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [0, 0, -65, -65, 0, -10, 12, 0, 0], 
                        [50, 50, 90, 90, 15, 5, 5, 15, 20], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [5, -47, -65, 25, -1, -10, 12, -11, -9], [50, 50, 90, 90, 15, 5, 5, 15, 20], ws_commu)
        time.sleep(period_1)


        if period_4 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [0, 0, -65, -65, 0, -10, 12, 0, 0], 
                        [50, 50, 90, 90, 15, 5, 5, 15, 20], ws_commu)
            time.sleep(period_4)

        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [47, -5, 25, -65, 1, -10, 12, 5, 13], [50, 50, 90, 90, 15, 5, 5, 15, 20], ws_commu)        
        time.sleep(period_3)

        if period_4 != 0:
            move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], 
                        [0, 0, -65, -65, 0, -10, 12, 0, 0], 
                        [50, 50, 90, 90, 15, 5, 5, 15, 20], ws_commu)
            time.sleep(period_4)
        move_multi_joint([5, 3, 4, 2, 7, 0, 6, 8, 1], [5, -47, -65, 25, -1, -10, 12, -11, -9], [50, 50, 90, 90, 15, 5, 5, 15, 20], ws_commu)
        time.sleep(period_3)

    elif emotion == 'no_talking':
        period_1 = period * 0.65
        period_2 = period * 0.35

        if period_2 != 0:
            move_multi_joint([3, 5, 6, 0], 
                        [0, 0, 0, 0], 
                        [20, 20, 5, 5], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 6, 0], [8, -8, 3, 2], [20, 20, 5, 5], ws_commu)
        time.sleep(period_1)


    elif emotion == 'talking':
        period_1 = period * 0.6
        period_2 = period * 0.35

        if period_2 != 0:
            move_multi_joint([3, 5, 6, 0], 
                        [0, 0, 5, 0], 
                        [20, 20, 5, 5], ws_commu)
            time.sleep(period_2)

        move_multi_joint([5, 3, 6, 0], [25, -25, 10, 5], [20, 20, 5, 5], ws_commu)
        time.sleep(period_1)

        # if period_2 != 0:
        #     move_multi_joint([3, 5, 6, 0], 
        #                 [0, 0, 5, 0], 
        #                 [20, 20, 5, 5], ws_commu)
        #     time.sleep(period_2)

        # move_multi_joint([5, 3, 6, 0], [25, -25, 10, 5], [20, 20, 5, 5], ws_commu)
        # time.sleep(period_1)