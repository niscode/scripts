from ws_utilze import *
import time


C = 0.6
H = 0.3

def happy_cylinder(x, speed, scale):
    # scale = scale * 0.5
    # speed ~ [0,0.5]
    # -1.2 * scale / period**2 * x**2 + 1.2 * scale/period * x
    scale = scale*1.5
    speed = speed * 1.5
    period = C/speed
    x = x % period
    v = (0.6 * scale)/period * ((-2.2 * x / period) + 1)
    # v = -(2.4 * scale) / period**2 + (1.2 * scale) / period

    return v, period


def happy_cylinder_skip(x, speed, scale):

    # speed ~ [0,0.5]
    # -1.2 * scale /period**2 *x **2 + 1.2 * scale/period * x
    # scale = scale * 0.5

    speed = speed * 1.5
    period1 = C/speed
    period2 = period1/2
    x = x % (period1+period2)
    if x < period1:
        v = (0.6 * scale)/period1 * ((-2.2 * x / period1) + 1)
        # v = -(2.4 * scale) / period1**2 + (1.2 * scale) / period2
    else:
        x = x - period1
        v = (0.2 * scale)/period2 * ((-2.2 * x / period2) + 1)
        # v = -(0.8 * scale) / period1**2 + (0.4 * scale) / period2

    return v, period1+period2


def neutral_cylinder(x, speed, scale):

    # speed ~ [0,0.5]

    period = C/speed
    c = (2*np.pi)/period
    v = np.cos(c*x) * scale * 0.2
    
    return v, period


def sad_cylinder(x, speed, scale):
    scale = scale * 0.5
     # speed ~ [0,0.5]
    period = (C/speed)
    c = (2*np.pi)/period
    v = np.cos(c*x) * scale * 0.1
    
    return v, period


def angry_cylinder(x, speed, scale):
    
     # speed ~ [0,0.5]
    speed = speed * 1.5
    speed = 2*speed
    scale = scale * 1.5
    period = (C/speed)
    x = x % period
    if x < (period/2):
        v = 0.3 * scale / period
        return v, period
    else:
        v = -0.35 * scale / period
        return v, period


def talking_cylinder(x, speed, scale):
    speed = speed*1.5
    period = C/speed
    c = (2*np.pi)/period
    v = np.cos(c*x) * scale * 0.2
    
    return v, period

def no_talking_cylinder(x, speed, scale):
    scale = scale*0.5

    period = C/speed
    c = (2*np.pi)/period
    v = np.cos(c*x) * scale * 0.08
    
    return v, period


def cylinderg_parameters(emotion, x, speed, scale):

    if emotion == "happy":
        return happy_cylinder(x, speed, scale)

    elif emotion == "neutral":
        return neutral_cylinder(x, speed, scale)

    elif emotion == "sad":
        return sad_cylinder(x, speed, scale)

    elif emotion == "angry":
        return angry_cylinder(x, speed, scale)
    
    elif emotion == "happy_skip":
        return happy_cylinder_skip(x, speed, scale)

    elif emotion == "talking":
        return talking_cylinder(x, speed, scale)
    
    elif emotion == "no_talking":
        return no_talking_cylinder(x, speed, scale)
