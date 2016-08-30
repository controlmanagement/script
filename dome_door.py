#! /usr/bin/env python

import time
import os
import sys
import argparse
import controller
import obs_log



# Info
# ----

name = 'dome_door'
description = 'Open or close the door of dome'

# Default parameters
# ------------------

open = ''

# Argument handler
# ================

p = argparse.ArgumentParser(description=description)
p.add_argument('--open', type=str,
               help='For open the door. Need 1.')
args = p.parse_args()
if args.open is not None: open = args.open

# Main
# ====

list = []
if open:
    list.append("--open")
    list.append(open)
obs_log.start_script(name, list)

ctrl = controller.controller()

if open:
    ctrl.dome_open()
    print("dome open")
else:
    ctrl.dome_close()
    print("dome close")

obs_log.end_script(name)

