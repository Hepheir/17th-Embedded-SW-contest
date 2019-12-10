# -*- coding: utf-8 -*-

import numpy as np
import cv2

import robo_color as color
import robo_camera as cam
import robo_serial as serial
import robo_debug as debug

import time
import math

class STATUS:
    LINE_MISSING = 'LINE MISSING'
    WALKING = 'WALKING'

    BRIDGE = 'BRIDGE'

    DRILL_CAN = 'DRILL-CAN'
    DRILL_PACK = 'DRILL-PACK'
# -----------------------------------------------
class STOP_MOTION:
    STABLE  = 10
    STAND   = 11
    LOWER   = 12
    LIMBO   = 13

class LOOP_MOTION:
    WALK_FORWARD = 32
    WALK_BACKWARD = 33
    WALK_LEFT = 34
    WALK_RIGHT = 35

    LOWER_FORWARD = 36
    LOWER_BACKWARD = 37
    LOWER_LEFT = 38
    LOWER_RIGHT = 39

    TURN_LEFT = 40
    TURN_RIGHT = 41

    TURN_LOWER_LEFT = 42
    TURN_LOWER_RIGHT = 43

class STEP:
    FORWARD = 64
    BACKWARD = 65
    LEFT = 9 # 66
    RIGHT = 8 # 67

    LOWER_FORWARD = 68
    LOWER_BACKWARD = 69
    LOWER_LEFT = 70
    LOWER_RIGHT = 71

    TURN_LEFT = 72
    TURN_RIGHT = 73

    TURN_LOWER_LEFT = 74
    TURN_LOWER_RIGHT = 75

class HEAD:
    # 좌우
    YAW_CENTER = 96
    YAW_LEFT_90 = 97
    YAW_RIGHT_90 = 98
    YAW_LEFT_45 = 99
    YAW_RIGHT_45 = 100
    
    # 상하
    PITCH_CENTER = 101
    PITCH_LOWER_45 = 102
    PITCH_LOWER_90 = 103

class ARM:
    DOWN = 112
    MID = 113
    UP = 114

class MACRO:
    SHUTTER = 128
    OPEN_DOOR = 129

    TEMP = 1
    
class SENSOR:
    DISTANCE = None # 적외선 센서 거리측정

line_tracing_sensitivity = 20
# -----------------------------------------------
def get(sensor):
    serial.TX_data(sensor)
    return serial.RX_data
# -----------------------------------------------
def objContTrace(mask, minObjSize=50):
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    if not contours:
        return []
    return list(filter(lambda c: cv2.contourArea(c) > minObjSize, contours))
# -----------------------------------------------
def center_of_contour(contour):
	# compute the center of the contour
    M = cv2.moments(contour)
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    return (cx, cy)
# -----------------------------------------------
def context(cmask):
    # 현재 로봇이 처한 상황을 파악
    if not stadingOnLine(cmask):
        return MACRO.TEMP # return to line
    
    if isEndOfLine(cmask):
        return endOfLine(cmask)
    
    # --------
    # if not findObstacles(cmask):
    #     return dirCalibration(cmask) # Running | Walking

    return dirCalibration(cmask) # undefined
    # --------

# -----------------------------------------------
def stadingOnLine(cmask):
    y_msk = cmask['yellow']
    conts = objContTrace(y_msk)
    return len(conts) > 0
# --------
def isEndOfLine(cmask):
    y_msk = cmask['yellow']
    roi = y_msk[:cam.HEIGHT*2//3,:]
    conts = objContTrace(roi)
    return len(conts) == 0
# --------
def endOfLine(cmask):
    y_msk = cmask['yellow'][cam.HEIGHT//2:,:]
    
    msk_l = y_msk[:,:cam.WIDTH//3]
    if len(objContTrace(msk_l)):
        return STEP.TURN_LEFT

    msk_r = y_msk[:,cam.WIDTH*2//3:]
    if len(objContTrace(msk_r)):
        return STEP.TURN_RIGHT

    # 문 / 셔터 / 림보인지 검사 시작
    return STOP_MOTION.LIMBO
# --------
def findObstacles(cmask):
    g_msk = cmask['green'][cam.HEIGHT*2//3:,:]
    r_msk = cmask['red'][cam.HEIGHT*2//3:,:]
    conts = objContTrace(g_msk) + objContTrace(r_msk)
    return len(conts) > 0
# -----------------------------------------------
def dirCalibration(cmask, prescaler=1/6):
    ltr_turn_sen = 30
    ltr_shift_sen = 30
    lowerh = int(cam.HEIGHT * prescaler)
    upperh = cam.HEIGHT - 1
    y_msk = cmask['yellow'][lowerh:,:]

    line_probs = objContTrace(y_msk)
    if not line_probs:
        return False

    line = max(line_probs, key=cv2.contourArea)
    vx,vy,x,y = cv2.fitLine(line, cv2.DIST_L2,0,0.01,0.01)

    if not vy:
        return False

    top_x = vx/vy * ( - y) + x
    bot_x = vx/vy * ((cam.HEIGHT + cam.CENTER[1]*2/3) - y) + x

    dx = (top_x - bot_x) / cam.WIDTH * 100
    bx = (bot_x - cam.CENTER[0]) / cam.CENTER[0] * 100
    print('%f, %f ' % (bx, dx))

    if abs(bx) + abs(dx) > 1000:
        return False

    # 위치 보정
    if abs(bx) > ltr_shift_sen:
        return STEP.RIGHT if bx > 0 else STEP.LEFT

    # 회전각 보정
    if abs(dx) > ltr_turn_sen:
        return STEP.TURN_RIGHT if dx > 0 else STEP.TURN_LEFT
        

    # 문제가 없으면 전진
    return LOOP_MOTION.WALK_FORWARD



    # 회전각 보정
    theta = 0 if (vx == 0) else math.atan(vy/vx)
    th = theta - np.pi/2

    if abs(th) > (np.pi/2 / ltr_turn_sen):
        return STEP.TURN_LEFT if (th > 0) else STEP.TURN_RIGHT
        
    # 위치 보정
    cx = center_of_contour(line)[0]/cam.CENTER[0] - 1
    if abs(cx) > (1 / ltr_shift_sen):
        return STEP.RIGHT if cx > 0 else STEP.LEFT

    # 문제가 없으면 전진
    return LOOP_MOTION.WALK_FORWARD


def walking():
    pass

def walking_green():
    pass


def findGreenObj(green_mask):
    # 초록 장애물을 발견하는 동작
    boxes = objTrace(green_mask)

def findBlueZone(blue_mask):
    pass


    