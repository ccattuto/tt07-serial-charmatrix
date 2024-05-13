#!/usr/bin/env python
import colorsys
import numpy as np

for h in np.arange(0, 360, 360/16):
    r, g, b = colorsys.hsv_to_rgb(h/360, 1, 0.8)
    print (f'{int(g*255):>08b}{int(r*255):>08b}{int(b*255):>08b}')