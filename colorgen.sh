#!/bin/sh
python colorgen.py  | awk '{print "colors[" NR-1 "] = 24\x27" "b" $1 ";"}'
