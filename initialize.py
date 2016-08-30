#! /usr/bin/env python

import time
import os
import sys
import argparse
import urllib2
import controller
import obs_log



# Info
# ----

name = 'initialize'
description = 'Initialize antenna'

# Default parameters
# ------------------

opt = ''

# Argument handler
# ================

p = argparse.ArgumentParser(description=description)
p.add_argument('--opt', type=str,
               help='For optical. Need 1.')

args = p.parse_args()

if args.opt is not None: opt = args.opt

# Main
# ====

obs_log.start_script(name)
obs_log.weather_log()

ctrl = controller.controller()
ctrl.drive_on()
print("dome_open")
ctrl.dome_open()

if opt:
    print("memb_open")
    ctrl.memb_open()
print("Init end")
ctrl.dome_track()

obs_log.end_script(name)

