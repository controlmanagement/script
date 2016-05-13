#-*- coding: utf-8 -*-
#presented by Hiroaki Iwamura
import time
import math
import antenna_nanten
import threading
import sys


class otf(object):
	
	
	def __init__(self):
		self.antenna = antenna_nanten.antenna_nanten()
		pass
	
	def otf_start(self, script, hosei):
		self.stop_thread = threading.Event()
		self.otf_thread = threading.Thread(target = self.otf, args = (script, hosei))
		self.otf_thread.start()
		return
	
	def otf_stop(self):
		print(1)
		self.stop_thread.set()
		print(2)
		self.otf_thread.join()
		print(3)
		self.antenna.otf_end()
		return
	
	def otf(self, script, hosei): # reference:[operator_otf.py]
		param = []
		c = 299792458*math.pow(10, 6)
		f = open(script)
		line = f.readline()
		
		#read scripts
		while line:
			line = line.replace("=", " ")
			list = line.split()
			if list[1] == "#":
				break
			param.append(list[1])
			line = f.readline()
		f.close()
		
		#param[2]=on_x, param[3]=on_y, param[4]=off_x, param[5]=off_y, param[6]=coord_mode, param[12]=start_x, param[13]=start_y, param[19]=n,
		#param[18]/(param[16]/param[15])=dt, param[25]/(param[16]/param[15])=rampt
		#delay=0 => for adjust time(OFF to ON time)
		if int(param[14]) == 0:
			dx = float(param[18])/3600.
			dy = 0
		else:
			dx = 0
			dy = float(param[18])/3600.
		dt = float(param[18])/(float(param[16])/float(param[15]))
		rampt = float(param[25])/(float(param[16])/float(param[15]))
		
		param[6] = param[6].lstrip('"')
		param[6] = param[6].rstrip('"')
		if param[6] == "j2000" or param[6] == "b1950":
			coord_sys = "EQUATRIAL"
			coord_mode = param[6].upper()
		else:
			coord_sys = param[6].upper()
			coord_mode = 0
			lamda = c/(float(param[39])*math.pow(10, 6))
		total_count = int(param[19])
		
		for scan_count in range(total_count):
			#OFF data
			if coord_sys == "EQUATRIAL":
				self.antenna.radec_move(float(param[4]), float(param[5]), coord_mode, lamda, float(param[20]), float(param[21]), hosei)
			elif coord_sys == "GALACTIC":
				self.antenna.galactic_move(float(param[4]), float(param[5]), lamda, float(param[20]), float(param[21]), hosei)
				time.sleep(0.1)
			ret = self.antenna.read_track()
			print("observe off")
			print("ret="+ret[0]+" "+ret[1])
			while ret[0] == "FALSE" or ret[1] == "FALSE":
				ret = self.antenna.read_track()
				time.sleep(0.5)
			#self.???.get_data
			self.antenna.tracking_end()
			
			print("b")
			#ON data
			if int(param[14]) == 0:
				sx = float(param[2]) + float(param[12])/3600.
				sy = float(param[3]) + float(param[13])/3600. + dx/3600.*scan_count
			else:
				sx = float(param[2]) + float(param[12])/3600. + dy/3600.*scan_count
				sy = float(param[3]) + float(param[13])/3600.
			
			start_x = sx-float(dx)/2.-float(dx)/float(dt)*rampt
			start_y = sy-float(dy)/2.-float(dy)/float(dt)*rampt
			
			print("start_x:"+str(start_x))
			print("start_y:"+str(start_y))
			
			if coord_sys == "EQUATRIAL":
				self.antenna.radec_move(start_x, start_y, coord_mode, lamda, float(param[0]), float(param[1]), hosei)
			elif coord_sys == "GALACTIC":
				self.antenna.galactic_move(start_x, start_y, lamda, float(param[0]), float(param[1]), hosei)
			time.sleep(0.1)
			ret = self.antenna.read_track()
			print("observe on")
			print("ret="+ret[0]+" "+ret[1])
			while ret[0] == "FALSE" or ret[1] == "FALSE":
				ret = self.antenna.track_check()
				if self.stop_thread.is_set():
					sys.exit()
				time.sleep(0.5)
			self.antenna.otf_tracking_end()
			stime = (40587 + time.time()/(24.*3600.))+(0+rampt)/24./3600. # 0 = delay ,for test
			#self.get_data(stime,???)    or stime from self.antenna.otf_start
			self.antenna.otf_start(sx, sy, 0, coord_sys, dx, dy, dt, int(param[19]), rampt, 0, lamda, hosei, coord_mode)
			#self.get_data(stime,???)
			
			print("line:"+str(scan_count))
			
			if self.stop_thread.is_set():
				print("c")
				sys.exit()
			print("d")
			
		self.antenna.otf_end()
		return



