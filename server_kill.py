#! /usr/bin/env python

import commands as cmd
import sys
sys.path.append("/home/amigos/NECST/script")
import obs_log


name = "server_kill"
list = []
obs_log.start_script(name, list)

ret = cmd.getoutput("kill `cat /home/amigos/NECST/soft/server/server_ctrl.pid`")
if ret:
    print("error:kill server_ctrl")
    print(ret)
ret = cmd.getoutput("kill `cat /home/amigos/NECST/soft/server/server_weather.pid`")
if ret:
    print("error:kill server_weather")
    print(ret)

obs_log.end_script(name)
