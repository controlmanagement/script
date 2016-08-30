#! /usr/bin/env python

import os
import time
import math
import argparse
import signal
from pyslalib import slalib
import ccd
import coord
import controller
import sys
import obs_log



# Info
# ----

name = 'onepoint_track'
description = 'Get optical onepoint tracking data'

# Default parameters
# ------------------

ra = 0.
dec = 0.
interval = 10.
duration = 60.

# Argument handler
# ================

p = argparse.ArgumentParser(description=description)
p.add_argument('--ra', type=float,
               help='Ra of target (degree).')
p.add_argument('--dec', type=float,
               help='Dec of target (degree).')
p.add_argument('--interval', type=float,
               help='Interval time (sec). default=%.1f'%(interval))
p.add_argument('--duration', type=float,
               help='Duration time (min). default=%.1f'%(duration))

args = p.parse_args()

if args.ra is not None: ra = args.ra
else:
    print("argument --ra is required")
    sys.exit()
if args.dec is not None: dec = args.dec
else:
    print("argument --dec is required")
    sys.exit()
if args.interval is not None: interval = args.interval
if args.duration is not None: duration = args.duration


# Main
# ====

list = []
list.append("--ra")
list.append(ra)
list.append("--dec")
list.append(dec)
list.append("--interval")
list.append(interval)
list.append("--duration")
list.append(duration)
obs_log.start_script(name, list)

tai_utc = 36.0 # tai_utc=TAI-UTC  2015 July from ftp://maia.usno.navy.mil/ser7/tai-utc.dat
dut1 = 0.14708

ctrl = controller.controller()
ctrl.dome_track()
coord = coord.coord_calc()
ccd = ccd.ccd_client("172.20.0.12", 8010)

def handler(num, flame):
    ctrl.tracking_end()
    print("!!ctrl + c!!")
    print("Stop antenna")
    sys.exit()

def calc_star_azel(ra, dec, mjd):
    ra = ra*math.pi/180.
    dec = dec*math.pi/180.
    
    ret = slalib.sla_map(ra, dec, 0, 0, 0, 0, 2000, mjd + (tai_utc + 32.184)/(24.*3600.))
    ret = list(ret)
    ret = slalib.sla_aop(ret[0], ret[1], mjd, dut1, -67.70308139*math.pi/180, -22.96995611*math.pi/180, 4863.85, 0, 0, 283, 500, 0.1, 0.5, tlr=0.0065)
    real_az = ret[0]
    real_el = math.pi/2. - ret[1]
       
    real_az = real_az*180./math.pi
    real_el = real_el*180./math.pi
    ret = coord.apply_kisa(real_az, real_el, "/home/amigos/NECST/soft/server/hosei_opt.txt")
    real_az += ret[0]
    real_el += ret[1]
    return [real_az, real_el]


timestamp = time.strftime('%Y%m%d_%H%M%S')
signal.signal(signal.SIGINT, handler)
ctrl.radec_move(ra, dec, "J2000", hosei = '/home/amigos/NECST/soft/server/hosei_opt.txt', lamda = 0.5)

#calc star az
tv = time.time()
mjd = tv/24./3600. + 40587.0
status = ctrl.read_status()
dome_az = status["Current_Dome"]
if dome_az < 0.:
    dome_az += 360.
target = calc_star_azel(ra, dec, mjd)
if target[0] < 0.:
    target[0] += 360.

#wait dome sync
while abs(dome_az - target[0]) > 10. and abs(dome_az - target[0]) < 350.:
    time.sleep(0.5)
    status = ctrl.read_status()
    dome_az = status["Current_Dome"]
    if dome_az < 0.:
        dome_az += 360.
    continue



e_time = 0

#start observation
while duration*60 > e_time:
    tv = time.time()
    mjd = tv/24./3600. + 40587.0
    status = ctrl.read_status()
    target = calc_star_azel(ra, dec, mjd)
    ret = ccd.onepoint_shot(0, 0, target[0], target[1], "opt_track_"+timestamp, status)
    if ret:
        print(ret)
        print("!!Can not find star!!")
    else:
        print("OK")
    tv2 = time.time()
    if tv2 -tv >= interval:
        e_time += tv2 -tv
    else:
        time.sleep(interval - (tv2 - tv))
        e_time += interval

ctrl.tracking_end()
ctrl.dome_track_end()
print("Finish observation")

obs_log.end_script(name)
