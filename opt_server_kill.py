#! /usr/bin/env python

import commands as cmd

ret = cmd.getoutput("kill `cat /home/amigos/NECST/soft/server/server_opt.pid`")
if ret:
    print("error:kill server_opt")
    print(ret)


