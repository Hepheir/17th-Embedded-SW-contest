# -*- coding: utf-8 -*-

import numpy as np
import cv2
# import serial

import time
import math


# CUSTOM =================================================

STATUS = {
    'debug' : -1,
    'stop' : 0,
    'line tracing' : 1
}

# bandwidth : lower, upper hsv를 파악하는데 사용.
COLOR_REF = {
    'line' : {
        'hsv' : (201,153,172),
        'bandwidth' : (102,82,166),
        'minArea' : 40
    },
    'yellow' : {
        'hsv' : (201,153,172),
        'bandwidth' : (102,82,166),
        'minArea' : 50
    },
    'red' : {
        'hsv' : (32,170,123),
        'bandwidth' : (66,60,56),
        'minArea' : 50
    },
    'blue' : {
        'hsv' : (85,80,108),
        'bandwidth' : (52,60,96),
        'minArea' : 10
    }
}
HIGHLIGHT = {
    'color' : (0,0,255),
    'thickness' : 5
}
VIEW_SIZE = { 'width' : 320, 'height' : 240 }
BPS = 4800


WINNAME = {
    'main' : 'main',
    'mask' : 'mask'
}
KEY = {
    'esc' : 27,
    'spacebar' : ord(' '),
    '0' : ord('0'),
    '1' : ord('1')
}

mouse = { 'x' : 0, 'y' : 0 }

# ============================================================

serial_use = False
serial_port =  None

system_pause = False

#-----------------------------------------------
def nothing(x):
    pass
#-----------------------------------------------
def create_blank(width, height):
    image = np.zeros((height, width, 3), dtype=np.uint8)
    return image
#-----------------------------------------------

# **************************************************
# **************************************************
# **************************************************
# **************************************************
# **************************************************
# **************************************************
# **************************************************
# **************************************************
# 84022014

if __name__ == '__main__':
    # -------- User Setting --------
    BPS =  4800  # 4800,9600,14400, 19200,28800, 57600, 115200
    
    # -------- Camera Load --------
    video = cv2.VideoCapture(0)
    time.sleep(0.5)

    if not video.isOpened():
        raise Exception("Could not open video device")
    
    video.set(cv2.CAP_PROP_FRAME_WIDTH,  VIEW_SIZE['width'])
    video.set(cv2.CAP_PROP_FRAME_HEIGHT, VIEW_SIZE['height'])

    # -------- Serial Setting --------
    serial_use = False # DEBUG

    if serial_use: #? Serial 통신 활성화 시, 미리 버퍼를 클리어
       serial_port = serial.Serial('/dev/ttyAMA0', BPS, timeout=0.001)
       serial_port.flush() # serial cls

    # -------- Screen Setting --------
    cv2.namedWindow(WINNAME['main'])
    cv2.namedWindow(WINNAME['mask'])

    # -------- Debug Preset --------
    current_status = STATUS['line tracing']

    # -------- Main Loop Start --------
    while True:
        # -------- Toggle System Mode --------
        key = cv2.waitKey(1) & 0xFF # [0xFF &] op. need for raspbian

        if key is KEY['spacebar']:
            # -- system : pause --
            system_pause = not system_pause

            if system_pause:
                print('paused')
            else:
                print('resumed')

        elif key is KEY['esc']:
            # -- system : exit --
            break

        elif key is KEY['1']:
            current_status = STATUS['line tracing']

        elif key is KEY['0']:
            current_status = STATUS['debug']

        if system_pause:
            continue

        # -------- Grab frames --------
        next_frame, current_frame = video.read()
        if not next_frame:
            break # no more frames to read : EOF

        # -------- Check Context --------
        # TODO : 현재 상황 파악 하는 부분
        # current_status = ?

        # -------- Action :: Debug --------
        if current_status == STATUS['debug']:
            # -- 커서가 가리키는 HSV 색상 --
            pointer_pos = (VIEW_SIZE['width']//2, VIEW_SIZE['height']*5//6)
            current_frame_hsv = cv2.cvtColor(current_frame, cv2.COLOR_BGR2HSV)

            cursor_hsv = current_frame_hsv[pointer_pos]
            cv2.circle(current_frame, pointer_pos, HIGHLIGHT['thickness'], HIGHLIGHT['color'])

            # -- key hold시, line색상으로 설정 --
            key = cv2.waitKey(1) & 0xFF
            if key is KEY['0']:
                COLOR_REF['line']['hsv'] = cursor_hsv
                print('Set line color as : ', COLOR_REF['line']['hsv'])

            cv2.imshow(WINNAME['main'], current_frame)

        # -------- Action :: Line Tracing --------
        elif current_status == STATUS['line tracing']:
            # TODO : 라인트레이싱 (급함, 우선순위 1)
            # ---- Region of Interest : 관심영역 지정 ----
            roi_frame = current_frame[VIEW_SIZE['height']*2//3 : VIEW_SIZE['height'], :]
            roi_frame_hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)

            # ---- Line 검출 ----
            line_hsv_lower = np.subtract(COLOR_REF['line']['hsv'], COLOR_REF['line']['bandwidth'])
            line_hsv_upper = np.add(COLOR_REF['line']['hsv'], COLOR_REF['line']['bandwidth'])

            # line_mask = cv2.inRange(roi_frame_hsv, line_hsv_lower, line_hsv_upper)
            gray = cv2.cvtColor(roi_frame,cv2.COLOR_BGR2GRAY)
            line_mask = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
            line_mask = cv2.morphologyEx(line_mask, cv2.MORPH_OPEN, kernel)


            retval = cv2.findContours(line_mask.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours,hierarchy = retval[1:3] if cv2.__version__.split('.')[0] == '3' else retval
            
            cv2.drawContours(roi_frame,contours,-1,HIGHLIGHT['color'],HIGHLIGHT['thickness'])

            cv2.imshow(WINNAME['mask'], line_mask)
            cv2.imshow(WINNAME['main'], current_frame)
        


    # cleanup the camera and close any open windows
    video.release()
    cv2.destroyAllWindows()

    if serial_use:
       serial_port.close()