# -*- coding: utf-8 -*-

SERIAL_USABLE = True

Serial = None # initialize with serial_init()
#-----------------------------------------------
try:
    import serial
except:
    SERIAL_USABLE = False

import robo_debug as debug
#-----------------------------------------------
def init(bps=4800):
    global Serial

    print('"robo_serial.py" initialized.')

    if not SERIAL_USABLE:
        print('    failed to import serial.')
        print('    >> serial disabled.')
        return None

    Serial = serial.Serial('/dev/ttyAMA0', bps, timeout=0.001) # sudo chmod 777 /dev/ttyAMA0
    Serial.flush() # serial cls
    print('    Successfully loaded serial.Serial')
    print('    >> Serial enabled.')
    return Serial
#-----------------------------------------------
def TX_data(byte):  # one_byte= 0~255
    if not SERIAL_USABLE:
        # print('[T] Serial is not available')
        return None
    
    Serial.write(chr(int(byte)))
    return True
#-----------------------------------------------
def RX_data():
    if not SERIAL_USABLE:
        # print('[R] Serial is not available')
        return None

    if Serial.inWaiting() <= 0:
        return None
    
    byte = Serial.read(1)
    return byte
