# -*- coding: utf-8 -*-

import numpy as np
import cv2

import robo_serial  as serial
import robo_camera  as cam
import robo_color   as color
import robo_move    as move
import robo_debug   as debug

import threading
import sys
import time

# 32cm h / 24 cm w

# ******************************************************************


# ******************************************************************

frame = None
key = None
key_chr = None

routine_stoppers = []

main_routine_time_s = 0.8
main_routine_args = {}

sub_routine_time_s = 1.2
sub_routine_args = {}

serial_queue = []

# ******************************************************************

@debug.setInterval(main_routine_time_s)
def main_routine(main_routine_args):
    global serial_queue
    cmasks = color.colorMaskAll(frame)
    action = move.context(cmasks)

    if not debug.DEBUG_MODE:
        del serial_queue[:]
        serial_queue.append(action)

    for x in [1,2,3]:
        x = cam.WIDTH*x//3 - 1
        cv2.line(frame, (x, 0), (x, cam.HEIGHT), (255,255,255), 1)
    for y in [1,2,3]:
        y = cam.HEIGHT*y//3 - 1
        cv2.line(frame, (0, y), (cam.WIDTH, y), (255,255,255), 1)

    main_routine_args['frame'] = frame
    main_routine_args['context'] = '?'
    main_routine_args['color_masks'] = cmasks
    main_routine_args['scmsk full'] = debug.stackedColorMasks(frame, main_routine_args['color_masks'])
    main_routine_args['scmsk 1/3'] = debug.stackedColorMasks(frame[cam.HEIGHT//2:,:], color.colorMaskAll(frame[cam.HEIGHT//2:,:]))


@debug.setInterval(sub_routine_time_s)
def sub_routine(sub_routine_args):
    if not serial_queue:
        sub_routine_args['tx_data'] = -1
    else:
        sub_routine_args['tx_data'] = serial_queue[0]

        del serial_queue[0]
        serial.TX_data(sub_routine_args['tx_data'])

# ******************************************************************
# ******************************************************************
# ******************************************************************
if __name__ == '__main__':
    serial.init()
    cam.init(0 if debug.isRasp() else '1.mp4')
    color.init()
    # --------
    serial_queue.append(move.HEAD.PITCH_LOWER_45)
    frame = cam.getFrame()
    key_chr = '_'

    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    recorder = cv2.VideoWriter('%s.avi' % time.ctime() ,fourcc, 15.0, cam.RESOLUTION)

    routine_stoppers.append( main_routine(main_routine_args) )
    routine_stoppers.append(  sub_routine( sub_routine_args) )

    time.sleep(max([main_routine_time_s, sub_routine_time_s]))
    # --------
    print('')
    print('Start mainloop')
    print('')
    while True:
        frame = cam.getFrame(imshow=True)
        recorder.write(frame)

        key = debug.waitKey(10)
        key_chr = chr(key) if key else key_chr
        # --------
        if key == 27: # ESC
            break
        elif key_chr == '`':
            key_chr = '_'
            debug.DEBUG_MODE = not debug.DEBUG_MODE
            continue
        # --------
        if key:
            remote = debug.remoteCtrl(key)
            if not (remote is None):
                serial_queue.append(remote)
        # --------
        try:
            debug._print('\r'+' '*64)
            debug._print('\r' +
                '[%s]' % debug.runtime_ms_str() +
                '[key=%c]' % key_chr +
                '[txq=%d]' % len(serial_queue) +
                '[tx0=%d]' % (serial_queue[0] if len(serial_queue) else -1) +
                '[d=%c]' % ('T' if debug.DEBUG_MODE else 'F') +
                str(serial_queue) + 
                ' ')
            cv2.imshow('frame', main_routine_args['frame'])
            cv2.imshow('scmsk full', main_routine_args['scmsk full'])
            cv2.imshow('scmsk 1/3', main_routine_args['scmsk 1/3'])
        except:
            pass


# ******************************************************************
# ******************************************************************
# ******************************************************************
cv2.destroyAllWindows()
for stop in routine_stoppers:
    stop.set()
time.sleep(max([main_routine_time_s, sub_routine_time_s]))

cam.Video.release()

print('')
print('')
print('Exit program')
print('')
