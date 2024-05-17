#!/usr/bin/env python
import sys
import serial
import time

s = serial.Serial(sys.argv[1], 9600, 8, "N", 1)

col = 0
for n in range(10000):
    msg = '%04d\n' % n
    if n % 100 == 0:
        col = (n // 100) % 16
        msg = chr(128+col) + msg
    s.write(msg.encode())
    time.sleep(0.1)

s.close()
