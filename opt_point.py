import math
import time
import datetime
import controller
import core.ccd
import signal
import sys
from pyslalib import slalib



class opt_point_controller(object):
    #reference : ccd.py, imageppm.cpp, imagepgm.cpp
    
    
    pointing_list = "/home/amigos/NECST/soft/core/pointing.list"
    tai_utc = 36.0 # tai_utc=TAI-UTC  2015 July from ftp://maia.usno.navy.mil/ser7/tai-utc.dat
    dut1 = 0.14708
    
    
    def __init__(self):
        self.ctrl = controller.controller()
        self.ccd = core.ccd.ccd_controller()
        return
    
    def handler(self, num, flame):
        print("!!ctrl+C!!")
        print("STOP MOVING")
        self.ctrl.tracking_end()
        sys.exit()
    
    def calc_star_azel(self, ra, dec, mjd):
        ra = ra*math.pi/180.
        dec = dec*math.pi/180.
        
        ret = slalib.sla_map(ra, dec, 0, 0, 0, 0, 2000, mjd + (self.tai_utc + 32.184)/(24.*3600.))
        ret = list(ret)
        ret = slalib.sla_aop(ret[0], ret[1], mjd, self.dut1, -67.70308139*math.pi/180, -22.96995611*math.pi/180, 4863.85, 0, 0, 283, 500, 0.1, 0.5, tlr=0.0065)
        real_az = ret[0]
        real_el = math.pi/2. - ret[1]
           
        real_az = real_az*180./math.pi
        real_el = real_el*180./math.pi
        return [real_az, real_el]
    
    def create_table(self):
        #create target_list
        
        f = open(self.pointing_list)
        line = f.readline()
        target_list = []
        tv = time.time()
        mjd2 = tv/24./3600. + 40587.0 # 40587.0 = MJD0
        
        
        #calculate mjd(now) and mjd(2000)
        date = datetime.datetime.today()
        ret = slalib.sla_cldj(date.year, date.month, date.day)
        mjd = ret[0]
        ret = slalib.sla_cldj(2000, 1, 1)
        mjd2000 = ret[0]
        
        while line:
            list = []
            line = line.replace(";", " ")
            line = line.split()
            
            #number(FK6)
            list.append(line[0])
            
            #ra,dec(degree)
            ra = float(line[1])*(360./24.)+float(line[2])*(360./24.)/60.+float(line[3])*(360./24.)/3600.+float(line[4])*(360./24.)/3600.*(mjd - mjd2000)/36525.
            if line[5] == "+":
                dec = float(line[6])+float(line[7])/60.+float(line[8])/3600.+float(line[9])/3600.*(mjd - mjd2000)/36525.
            else:
                dec = -(float(line[6])+float(line[7])/60.+float(line[8])/3600.)+float(line[9])/3600.*(mjd - mjd2000)/36525.
            list.append(ra)
            list.append(dec)
            list.append(line[21]) #magnitude
            
            ret = self.calc_star_azel(ra, dec, mjd2)
            list.append(ret[0]) #az
            #list = [number, ra, dec, magnitude, az]
            
            #print(ret[1])
            print(str(ra)+"  "+str(dec))
            
            if ret[1] >= 30 and ret[1] <= 80:
                print("============")
                num = len(target_list)
                if num == 0:
                    target_list.append(list)
                elif num == 1:
                    if target_list[0][4] < list[4]:
                        target_list.append(list)
                    else:
                        target_list.insert(0, list)
                else:
                    for i in range(num):
                        if target_list[i][4] > list[4]:
                            target_list.insert(i, list)
                            break
                        if i == num-1:
                            target_list.insert(num, list)
            
            #print(target_list)
            line = f.readline()
        
        f.close()
        return target_list
    
    def start_observation(self):
        signal.signal(signal.SIGINT, self.handler)
        table = self.create_table()
        num = len(table)
        
        print(table)
        
        date = datetime.datetime.today()
        month = str("{0:02d}".format(date.month))
        day = str("{0:02d}".format(date.day))
        hour = str("{0:02d}".format(date.hour))
        minute = str("{0:02d}".format(date.minute))
        second = str("{0:02d}".format(date.second))
        data_name = "opt_"+str(date.year)+month+day+hour+minute+second
        
        
        for i in range(num):
            tv = time.time()
            mjd2 = tv/24./3600. + 40587.0 # 40587.0 = MJD0
            
            #calculate Az and El for check
            ret = self.calc_star_azel(table[i][1], table[i][2], mjd2)
            real_el = ret[1]
            
            if real_el >= 30. and real_el <= 80.:
                self.ctrl.radec_move(table[i][1], table[i][2], "J2000", 0, 0, hosei = 'hosei_opt.txt', offcoord = 'HORIZONTAL', lamda = 0.5)
                print(table[i][1], table[i][2])
                print(ret)
                
                #track_flag = ["TRUE", "TRUE"] #for test
                track_flag = self.ctrl.read_track()
                #wait track
                while track_flag[0] == "FALSE" or track_flag[1] == "FALSE":
                    time.sleep(0.5)
                    track_flag = self.ctrl.read_track()
                    continue
                
                status = self.ctrl.read_status()
                dome_az = status["Current_Dome"]
                if dome_az < 0.:
                    dome_az += 360.
                target_az = ret[0]
                if target_az < 0.:
                    target_az += 360.
                while abs(dome_az - target_az) > 10.:
                    time.sleep(0.5)
                    status = self.ctrl.read_status()
                    dome_az = status["Current_Dome"]
                    if dome_az < 0.:
                        dome_az += 360.
                    continue
                
                tv = time.time()
                mjd2 = tv/24./3600. + 40587.0
                n_star = self.calc_star_azel(table[i][1], table[i][2], mjd2)
                self.ccd.all_sky_shot(table[i][0], table[i][3], n_star[0], n_star[1], data_name, status)
            else:
                #out of range(El)
                pass
        self.ctrl.tracking_end()
        print("OBSERVATION END")
        return
    
    
