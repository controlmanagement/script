#! /usr/bin/env python

import time
import urllib2


# Info
# ----

"""
name = 'obs_log'
description = 'Logging observation'
"""

# Main
# ====

def start_script(name, list):
    tstmp = time.strftime("%H:%M:%S")
    daystmp = time.strftime("%Y%m%d")
    f = open("/home/amigos/NECST/script/data/obs_log/"+daystmp+".txt", "a")
    f.write("- "+tstmp+" start:"+name+"\n")
    num = len(list)
    if num != 0:
        for i in range(num/2):
            f.write(" %s %s\n" %(list[i*2], list[i*2+1]))
    f.close()

def end_script(name, file = ""):
    tstmp = time.strftime("%H:%M:%S")
    daystmp = time.strftime("%Y%m%d")
    f = open("/home/amigos/NECST/script/data/obs_log/"+daystmp+".txt", "a")
    f.write("-- "+tstmp+" end:"+name+"\n")
    if file:
        f.write("-- data:"+file+"\n")
    f.close()

def weather_log():
    tstmp = time.strftime("%Y/%m/%d %H:%M:%S")
    daystmp = time.strftime("%Y%m%d")
    text = []
    fp = urllib2.urlopen("http://200.91.8.66/WeatherMonitor/WeatherMenu.html")
    html = fp.readline()
    while html:
        html=str(html)
        html.replace(">", " ")
        text.append(html)
        html = fp.readline()
    fp.close()
    
    in_temp = text[23].split()
    out_temp = text[27].split(">")
    out_temp = out_temp[1].split()
    d_temp = text[31].split()
    c_temp = text[35].split()
    in_humi = text[39].split(">")
    in_humi = in_humi[1].split()
    out_humi = text[43].split(">")
    out_humi = out_humi[1].split()
    wind_dir = text[47].split(">")
    wind_dir = wind_dir[1].split()
    wind_speed = text[51].split()
    press = text[55].split(">")
    press = press[1].split()
    
    f = open("/home/amigos/NECST/script/data/obs_log/"+daystmp+".txt", "a")
    f.write("\n")
    f.write("- Weather\n")
    f.write(" %s [JST]" %(tstmp))
    f.write(" In Temp %s [C]\n" %(in_temp[2]))
    f.write(" Out Temp %s [C]\n" %(out_temp[0]))
    f.write(" Dome Temp %s [C]\n" %(d_temp[2]))
    f.write(" Cab Temp %s [C]\n" %(c_temp[2]))
    f.write(" In Humi %s [%s]\n" %(in_humi[0], "%"))
    f.write(" Out Humi %s [%s]\n" %(out_humi[0], "%"))
    f.write(" Wind Dir %s [deg]\n" %(wind_dir[0]))
    f.write(" Wind Sp %s [m/s]\n" %(wind_speed[2]))
    f.write(" Pressure %s [hPa]\n" %(press[0]))
    f.write("\n")
    f.close()
    
