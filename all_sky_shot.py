#! /usr/bin/env python

import os
import time
import argparse
import opt_point
import sys
sys.path.append("/home/amigos/NECST/soft/log")
import drive_log
"""
import signal
def handler(num, flame):
    print("\n")
    print("observation_end")
    try:
        obs_drive.thread_end()
        print("thread_stop")
    except:
        print("no thread")
    sys.exit()
signal.signal(signal.SIGINT, handler)
"""


# Info
# ----

name = 'all_sky_shot'
description = 'Get all sky shot data'

# Default parameters
# ------------------



# Argument handler
# ================

p = argparse.ArgumentParser(description=description)

# Main
# ====

tstmp = time.strftime("%H%M%S")
daystmp = time.strftime("%Y%m%d")
f = open("./data/obs_log/"+daystmp+".txt", "a")
f.write(tstmp+" all_sky_shot.py\n")
f.close()


drive = drive_log.drive_log()
drive.thread_start()
opt = opt_point.opt_point_controller()
opt.start_observation()

