#! /usr/bin/env python

import time
import os
import sys
import argparse
import controller
import ccd
import signal


# Info
# ----

name = 'oneshot'
description = 'Get oneshot data'

# Default parameters
# ------------------

star = ''
memo = ''

# Argument handler
# ================

p = argparse.ArgumentParser(description=description)
p.add_argument('--star', type=str,
               help='Name of 1st magnitude star.(No space)')
p.add_argument('--memo', type=str,
               help='Working memo. This will be include in directroy name.')

args = p.parse_args()

if args.star is None:
    print('!!Star name is None!!')
    sys.exit()
else:
    star = args.star
if args.memo is not None: memo = args.memo


# Main
# ====

tstmp = time.strftime("%H%M%S")
daystmp = time.strftime("%Y%m%d")
f = open("./data/obs_log/"+daystmp+".txt", "a")
f.write(tstmp+" oneshot.py "+star+"\n")
f.close()

timestamp = time.strftime('%Y%m%d_%H%M%S') #time.strftime("%Y%m%d_%H%M%S", time.gmtime())
timestamp = timestamp+memo
star_list = []
planet_list = {"MERCURY":1, "VENUS":2, "MARS":4, "JUPITER":5, "SATURN":6, "URANUS":7, "NEPTUNE":8}
planet = 0
target = []

#read star list
f = open("/home/amigos/NECST/script/1st_star_list.txt")
line = f.readline()
while line:
    line = line.split()
    star_list.append(line)
    line = f.readline()

for i in range(len(star_list)):
    if star_list[i][0].upper() == star.upper():
        target.append(float(star_list[i][1]))
        target.append(float(star_list[i][2]))

if len(target) == 0:
    if star.upper() in planet_list:
        planet = planet_list[star.upper()]
    else:
        print('!!Can not find the name of star!!')
        sys.exit()

ccd = ccd.ccd_client("172.20.0.12", 8010)
ctrl = controller.controller()

def handler(num, flame):
    ctrl.tracking_end()
    print("!!ctrl + c!!")
    print("Stop antenna")
    sys.exit()


signal.signal(signal.SIGINT, handler)
ctrl.dome_track()
ctrl.tracking_end()
if planet:
    ctrl.planet_move(planet, hosei = "hosei_opt.txt", lamda = 0.5)
else:
    ctrl.radec_move(target[0], target[1], 'J2000', 0, 0, 'hosei_opt.txt', lamda = 0.5)

b_az = 0
while 1:
    status = ctrl.read_status()
    dome_az = status["Current_Dome"] 
    if dome_az < 0.:
        dome_az += 360.
    ant_az = status["Current_Az"]
    if ant_az < 0.:
        ant_az += 360.
    if abs(ant_az - dome_az) < 10. or abs(ant_az - dome_az) > 350.:
        ret = ctrl.read_track()
        if ret:
            break
    
    
    time.sleep(0.1)

ccd.oneshot(timestamp)
print(timestamp)

ctrl.dome_track_end()
ctrl.tracking_end()
print("Finish observation")

