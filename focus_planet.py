#! /usr/bin/env python
# coding:utf-8


# Configurations
# ==============
# Info
# ----

name = 'focus_planet'
description = 'Get P/S spectrum'


# Default parameters
# ------------------
obsfile = ''
tau = 0.0


# Argument handler
# ================

#編集中
import argparse

p = argparse.ArgumentParser(description=description)
p.add_argument('--obsfile', type=str,
               help='absolute path for obsfile')
p.add_argument('--tau', type=float,
               help='tau. default=%.1f'%(tau))

args = p.parse_args()

if args.obsfile is not None: obsfile = args.obsfile
if args.tau is not None: tau = args.tau

# Main
# ====
import os
import time
import numpy
#import doppler_nanten
#dp = doppler_nanten.doppler_nanten()
import controller
import obs_log

# subref
#import telescope_nanten.m2
#m = telescope_nanten.m2.m2_controller()
#m.open()
#m.get_pos()

list = []
list.append("--obsfile")
list.append(obsfile)
obs_log.start_script(name, list)

con = controller.controller()
con.dome_track()
import signal
def handler(num, flame):
    print("!!ctrl+C!!")
    print("STOP MOVING")
    con.tracking_end()
    sys.exit()
signal.signal(signal.SIGINT, handler)

obsdir = '/home/amigos/NECST/script/obslist/ps/'
obs_items = open(obsdir+obsfile, 'r').read().split('\n')
obs = {}
for _item in obs_items:
    print(_item)
    if _item.startswith('script;'): break
    _item = _item.split('#')[0]
    _key, _value = _item.split('=', 1)
    _key = _key.strip()
    _value = _value.strip()
    try:
        obs[_key] = eval(_value)
    except NameError:
        obs[_key] = obs[_value]
        pass
    continue

integ_on = obs['exposure']
integ_off = obs['exposure_off']
#ra = obs['lambda_on']#on点x座標
#dec = obs['beta_on']#on点y座標
#offx = obs['lambda_off']#off点x座標
#offy = obs['beta_off']#off点y座標
if obs['otadel'].lower() == 'y':
    offset_dcos = 1
else:
    offset_dcos = 0
#if obs['otadel_off'].lower() == 'y':
    #offset_dcos_off = 1
#else:
    #offset_dcos_off = 0

if obs['coordsys'].lower() == 'j2000' or obs['coordsys'].lower() == 'b1950':
        print('Please use position_switching.py')
        sys.exit()
elif obs['coordsys'].lower() == 'galactic':
        print('Please use position_switching.py')
        sys.exit()
elif obs['coordsys'].lower() == 'jupiter':
    	 coord_sys = 'jupiter'
    	 number = 5 #惑星番号                                           


else:
    print('Error:coordsys')
    con.tracking_end()
    sys.exit()
if obs['lo1st_sb_1'] == 'U':#後半に似たのがあるけど気にしない()               
   sb1 = 1
else:
    sb1 = -1
if obs['lo1st_sb_2'] == 'U':#後半に似たのがあるけど気にしない()               
    sb2 = 1
else:
    sb2 = -1  


# Initial configurations
# ----------------------

datahome = 'data'
timestamp = time.strftime('%Y%m%d_%H%M%S')
dirname = timestamp
savedir = os.path.join(datahome, name, dirname)

print('mkdir {savedir}'.format(**locals()))
os.makedirs(savedir)

# Data aquisition
# ---------------

d1_list = []
d2_list = []
tdim6_list = []
date_list = []
tsys_list = []
thot_list = []
tcold_list = []
vframe_list = []
vframe2_list = []
lst_list = []
az_list = []
el_list = []
tau_list = []
hum_list = []
tamb_list = []
press_list = []
windspee_list = []
winddire_list = []
sobsmode_list = []
mjd_list = []
secofday_list = []
subref_list = []
_2NDLO_list1 = []
_2NDLO_list2 = []

print('Start experimentation')
print('')

savetime = con.read_status()['Time']
num = 0
n = int(obs['nSeq'])
latest_hottime = 0
while num < n: 
    print('observation :'+str(num+1))
        
    print('tracking start')
    con.tracking_end()
    
    if obs['coordsys'].lower() == 'j2000' or obs['coordsys'].lower() == 'b1950':
        print('Please use position_switching.py')
        sys.exit()
    elif obs['coordsys'].lower() == 'galactic':
        print('Please use position_switching.py')
        sys.exit()
    elif coord_sys == 'jupiter':
        con.planet_move(5, off_x=obs['lamdel_off'], off_y=obs['betdel_off'], offcoord = obs['cosydel'])
    print('moving...')

    while not con.read_track():
        time.sleep(0.001)
        continue
    status = con.read_status()
    dome_az = status["Current_Dome"]
    if dome_az < 0.:
        dome_az += 360.
    ant_az = status["Current_Az"]
    if ant_az < 0.:
        ant_az += 360.
    while abs(dome_az - ant_az) > 3. and abs(dome_az - ant_az) < 357.:
        time.sleep(0.5)
        status = con.read_status()
        dome_az = status["Current_Dome"]
        if dome_az < 0.:
            dome_az += 360.
        ant_az = status["Current_Az"]
        if ant_az < 0.:
            ant_az += 360.

    print('tracking OK')
    _now = time.time()
    if _now > latest_hottime+60*obs['load_interval']:
        print('R')
        con.move_hot('in')
        
        temp = float(con.read_status()['CabinTemp1']) + 273.15
        
        print('Temp: %.2f'%(temp))
        print('get spectrum...')
        #dp1 = dp.set_track(obs['lambda_on'], obs['beta_on'], obs['vlsr'], obs['coordsys'], obs['lamdel'], obs['betdel'], offset_dcos, obs['cosydel'], integ_off*2+integ_on, obs['restfreq_1']/1000., obs['restfreq_2']/1000., sb1, sb2, 8038.000000000/1000., 9301.318999999/1000.)
        #lambel_off,betdel_offかも？SYNTHが固定値の場合
        #print(dp1[0])
        d = con.oneshot(exposure=integ_off)
        d1 = d['dfs1'][0]
        d2 = d['dfs2'][0]
        d1_list.append(d1)
        d2_list.append(d2)
        tdim6_list.append([16384,1,1])
        date_list.append(con.read_status()['Time'])
        thot_list.append(temp)
        vframe_list.append#(dp1[0])
        vframe2_list.append#(dp1[0])
        lst_list.append(con.read_status()['LST'])
        az_list.append(con.read_status()['Current_Az'])
        el_list.append(con.read_status()['Current_El'])
        tau_list.append(tau)
        hum_list.append(con.read_status()['OutHumi'])
        tamb_list.append(con.read_status()['OutTemp'])
        press_list.append(con.read_status()['Press'])
        windspee_list.append(con.read_status()['WindSp'])
        winddire_list.append(con.read_status()['WindDir'])
        sobsmode_list.append('HOT')
        mjd_list.append(con.read_status()['MJD'])
        secofday_list.append(con.read_status()['Secofday'])
        subref_list.append(con.read_status()['Current_M2'])
        latest_hottime = time.time()
        P_hot = numpy.sum(d1)
        tsys_list.append(0)
        _2NDLO_list1.append#(dp1[3]['sg21']*1000)
        _2NDLO_list2.append#(dp1[3]['sg22']*1000)
        #print(dp1[3]['sg21']*1000)
        #print(dp1[3]['sg22']*1000)
        pass

        #if latest_hottime > _now:
        #pass

    #print(dp1)
    print('OFF')
    con.move_hot('out')
    print('get spectrum...')

    temp = float(con.read_status()['CabinTemp1']) + 273.15
    d = con.oneshot(exposure=integ_off)
    d1 = d['dfs1'][0]
    d2 = d['dfs2'][0]
    d1_list.append(d1)
    d2_list.append(d2)
    tdim6_list.append([16384,1,1])
    date_list.append(con.read_status()['Time'])
    thot_list.append(temp)
    vframe_list.append#(dp1[0])
    vframe2_list.append#(dp1[0])
    lst_list.append(con.read_status()['LST'])
    az_list.append(con.read_status()['Current_Az'])
    el_list.append(con.read_status()['Current_El'])
    tau_list.append(tau)
    hum_list.append(con.read_status()['OutHumi'])
    tamb_list.append(con.read_status()['OutTemp'])
    press_list.append(con.read_status()['Press'])
    windspee_list.append(con.read_status()['WindSp'])
    winddire_list.append(con.read_status()['WindDir'])
    sobsmode_list.append('OFF')
    mjd_list.append(con.read_status()['MJD'])
    secofday_list.append(con.read_status()['Secofday'])
    subref_list.append(con.read_status()['Current_M2'])
    P_sky = numpy.sum(d1)
    tsys = temp/(P_hot/P_sky-1)
    tsys_list.append(tsys)
    _2NDLO_list1.append#(dp1[3]['sg21']*1000)
    _2NDLO_list2.append#(dp1[3]['sg22']*1000)
    #print(dp1[3]['sg21']*1000)
    #print(dp1[3]['sg22']*1000)

    print('move ON')
    con.tracking_end()

    if obs['coordsys'].lower() == 'j2000' or obs['coordsys'].lower() == 'b1950':
        print('Please use position_switching.py')
        sys.exit()
    elif obs['coordsys'].lower() == 'galactic':
        print('Please use position_switching.py')
    elif coord_sys == 'jupiter':
        con.planet_move(5, off_x=0, off_y=0, offcoord = obs['cosydel'])
    
    while not con.read_track():
        time.sleep(0.001)
        continue
    status = con.read_status()
    dome_az = status["Current_Dome"]
    if dome_az < 0.:
        dome_az += 360.
    ant_az = status["Current_Az"]
    if ant_az < 0.:
        ant_az += 360.
    while abs(dome_az - ant_az) > 3. and abs(dome_az - ant_az) < 357.:
        time.sleep(0.5)
        status = con.read_status()
        dome_az = status["Current_Dome"]
        if dome_az < 0.:
            dome_az += 360.
        ant_az = status["Current_Az"]
        if ant_az < 0.:
            ant_az += 360.

    print('tracking OK')
    
    print('ON')     

    print('get spectrum...')
    #print(dp1)
    temp = float(con.read_status()['CabinTemp1']) + 273.15
    d = con.oneshot(exposure=integ_on)
    d1 = d['dfs1'][0]
    d2 = d['dfs2'][0]
    d1_list.append(d1)
    d2_list.append(d2)
    tdim6_list.append([16384,1,1])
    date_list.append(con.read_status()['Time'])
    thot_list.append(temp)
    vframe_list.append#(dp1[0])
    vframe2_list.append#(dp1[0])
    lst_list.append(con.read_status()['LST'])
    az_list.append(con.read_status()['Current_Az'])
    el_list.append(con.read_status()['Current_El'])
    tau_list.append(tau)
    hum_list.append(con.read_status()['OutHumi'])
    tamb_list.append(con.read_status()['OutTemp'])
    press_list.append(con.read_status()['Press'])
    windspee_list.append(con.read_status()['WindSp'])
    winddire_list.append(con.read_status()['WindDir'])
    sobsmode_list.append('ON')
    mjd_list.append(con.read_status()['MJD'])
    secofday_list.append(con.read_status()['Secofday'])
    subref_list.append(con.read_status()['Current_M2'])
    tsys_list.append(tsys)
    _2NDLO_list1.append#(dp1[3]['sg21']*1000)    
    _2NDLO_list2.append#(dp1[3]['sg22']*1000)
    #print(dp1[3]['sg21']*1000)
    #print(dp1[3]['sg22']*1000)


    print('stop')
    con.tracking_end()
        
    num += 1
    continue

print('R')#最初と最後をhotではさむ
con.move_hot('in')
            
temp = float(con.read_status()['CabinTemp1']) + 273.15
        
print('Temp: %.2f'%(temp))
print('get spectrum...')
d = con.oneshot(exposure=integ_off)
d1 = d['dfs1'][0]
d2 = d['dfs2'][0]
d1_list.append(d1)
d2_list.append(d2)
tdim6_list.append([16384,1,1])
date_list.append(con.read_status()['Time'])
thot_list.append(temp)
vframe_list.append#(dp1[0])
vframe2_list.append#(dp1[0])
lst_list.append(con.read_status()['LST'])
az_list.append(con.read_status()['Current_Az'])
el_list.append(con.read_status()['Current_El'])
tau_list.append(tau)
hum_list.append(con.read_status()['OutHumi'])
tamb_list.append(con.read_status()['OutTemp'])
press_list.append(con.read_status()['Press'])
windspee_list.append(con.read_status()['WindSp'])
winddire_list.append(con.read_status()['WindDir'])
sobsmode_list.append('HOT')
mjd_list.append(con.read_status()['MJD'])
secofday_list.append(con.read_status()['Secofday'])
subref_list.append(con.read_status()['Current_M2'])
P_hot = numpy.sum(d1)
tsys_list.append(0)
_2NDLO_list1.append#(dp1[3]['sg21']*1000)
_2NDLO_list2.append#(dp1[3]['sg22']*1000)
con.move_hot('out')



if obs['lo1st_sb_1'] == 'U':
    ul = 1
else:
    ul = -1
imagfreq1 = obs['obsfreq_1'] - ul*obs['if1st_freq_1']*2  
lofreq1 = obs['obsfreq_1'] - ul*obs['if1st_freq_1']*1

if obs['lo1st_sb_1'] == 'U':
    ul1_1 = +1
else:
    ul1_1 = -1
if obs['lo2nd_sb_1'] == 'U':
    ul1_2 = +1
else:
    ul1_2 = -1
if obs['lo3rd_sb_1'] == 'U':
    ul1_3 = +1
else:
    ul1_3 = -1
ul1 = ul1_1 * ul1_2 * ul1_3
print(ul1)
cdelt1_1 = (-1)*ul1*0.079370340319607024 #[(km/s)/ch]
#dv1 = (300000*cdelt1_1)/obs['restfreq_1']
crpix1_1 = 8191.5 - obs['vlsr']/cdelt1_1 - (500-obs['if3rd_freq_1'])/0.061038881767686015


if obs['lo1st_sb_2'] == 'U':
    ul = 1
else:
    ul = -1
imagfreq2 = obs['obsfreq_2'] - ul*obs['if1st_freq_2']*2
lofreq2 = obs['obsfreq_2'] - ul*obs['if1st_freq_2']*1

if obs['lo1st_sb_2'] == 'U':
    ul2_1 = +1
else:
    ul2_1 = -1
if obs['lo2nd_sb_2'] == 'U':
    ul2_2 = +1
else:
    ul2_2 = -1
if obs['lo3rd_sb_2'] == 'U':
    ul2_3 = +1
else:
    ul2_3 = -1
ul2 = ul2_1 * ul2_2 * ul2_3
print(ul2)
cdelt1_2 = (-1)*ul2*0.0830267951512371 #[(km/s)/ch]                           
#dv2 = (300000*cdelt2)/obs['restfreq_2']
crpix1_2 = 8191.5 - obs['vlsr']/cdelt1_2 - (500-obs['if3rd_freq_2'])/0.061038881767686015

#d1list
read1 = {
    "OBJECT" : obs['object'],
    "BANDWID" : 1000000000, #デバイスファイルに追加
    "DATE-OBS" : date_list, 
    "EXPOSURE" : obs['exposure'],
    "TSYS" : tsys_list,
    "DATA" : d1_list,
    "TDIM6" : tdim6_list, #デバイスファイルに追加
    "TUNIT6" : 'counts', #デバイスファイルに追加
    "CTYPE1" : 'km/s', #デバイスファイルに追加
    "CRVAL1" : 0, #デバイスファイルに追加
    "CRPIX1" : crpix1_1, #デバイスファイルに追加
    "CDELT1" : cdelt1_1, #デバイスファイルに追加
    "CTYPE2" : 'deg', #未使用
    "CRVAL2" : 0, #未使用
    "CTYPE3" : 'deg', #未使用
    "CRVAL3" : 0, #未使用
    "T_VLSR" : 0, #未使用
    "OBSERVER" : obs['observer'],
    "SCAN" : 1, #要確認
    "OBSMODE" : obs['obsmode'],
    "MOLECULE" : obs['molecule_1'],
    "TRANSITI" : obs['transiti_1'],
    "TEMPSCAL" : 'TA', #未使用
    "FRONTEND" : 'nagoyaRX', #デバイスファイルに追加
    "BACKEND" : 'nagoyaDFS', #デバイスファイルに追加
    "THOT" : thot_list,
    "TCOLD" : 0, #tcold_list
    "FREQRES" : 0.06103515625, #デバイスファイルに追加[MHz]
    "TIMESYS" : 'UTC', #要確認
    "VELDEF" : 'RADI-LSR',
    "VFRAME" : vframe_list,
    "VFRAME2" : vframe2_list,
    "OBSFREQ" : obs['restfreq_1'], #restfreq_1
    "IMAGFREQ" : imagfreq1, #要計算
    "LST" : lst_list,
    "AZIMUTH" : az_list,
    "ELEVATIO" : el_list,
    "TAU" : tau_list,
    "HUMIDITY" : hum_list,
    "TAMBIENT" : tamb_list,
    "PRESSURE" : press_list,
    "WINDSPEE" : windspee_list,
    "WINDDIRE" : winddire_list,
    "BEAMEFF" : 1, #未使用
    "RESTFREQ" : obs['restfreq_1'],
    "SIG" : 'T', #未使用
    "CAL" : 'F', #未使用
    "SOBSMODE" : sobsmode_list,
    "QUALITY" : 1, #未使用
    "AOSLEN" : 0.04, #未使用
    "LOFREQ" : lofreq1, #要計算
    "SYNTH" : 8038.000000000,#要調査[MHz;IF1]2ndLO
    "FREQSWAM" : 0,#要調査
    "COORDSYS" : obs['coordsys'],
    "COSYDEL" : obs['cosydel'],
    "LAMDEL" : obs['lamdel'],
    "BETDEL" : obs['betdel'],
    "OTADEL" : obs['otadel'],
    "OTFVLAM" : 0,
    "OTFVBET" : 0,
    "OTFSCANN" : 0,
    "OTFLEN" : 0,
    "SUBSCAN" : 0, # 要実装
    "MJD" : mjd_list,
    "SECOFDAY" : secofday_list,
    "SIDEBAND" : obs['lo1st_sb_1'],
    "_2NDSB" : obs['lo2nd_sb_1'],
    "_3RDSB" : obs['lo3rd_sb_1'],
    "_2NDLO" : _2NDLO_list1,#ドップラーシフト込み
    "_3RDLO" : obs['lo3rd_freq_1'],
    "SUBREF" : subref_list,
    "LOCKSTAT" : 'F'#未使用
    }

#d2_list
#d1list                                                                        

read2 = {
    "OBJECT" : obs['object'],
    "BANDWID" : 1000000000, #デバイスファイルに追加
    "EXPOSURE" : obs['exposure'],
    "DATE-OBS" : date_list, 
    "TSYS" : tsys_list,
    "DATA" : d2_list,
    "TDIM6" : tdim6_list, #デバイスファイルに追加
    "TUNIT6" : 'counts', #デバイスファイルに追加
    "CTYPE1" : 'km/s', #デバイスファイルに追加 
    "CRVAL1" : 0, #デバイスファイルに追加
    "CRPIX1" : crpix1_2, #デバイスファイルに追加
    "CDELT1" : cdelt1_2, #デバイスファイルに追加
    "CTYPE2" : 'deg', #未使用
    "CRVAL2" : 0, #未使用
    "CTYPE3" : 'deg', #未使用
    "CRVAL3" : 0, #未使用
    "T_VLSR" : 0, #未使用
    "OBSERVER" : obs['observer'],
    "SCAN" : 1, #要確認
    "OBSMODE" : obs['obsmode'],
    "MOLECULE" : obs['molecule_2'],
    "TRANSITI" : obs['transiti_2'],
    "TEMPSCAL" : 'TA', #未使用
    "FRONTEND" : 'nagoyaRX', #デバイスファイルに追加
    "BACKEND" : 'nagoyaDFS', #デバイスファイルに追加                           
    "THOT" : thot_list,
    "TCOLD" : 0, #tcold_list                                                 
    "FREQRES" : 0.06103515625, #デバイスファイルに追加[MHz]                
    "TIMESYS" : 'UTC', #要確認                                                 
    "VELDEF" : 'RADI-LSR',
    "VFRAME" : vframe_list,
    "VFRAME2" : vframe2_list,
    "OBSFREQ" : obs['restfreq_2'],                                
    "IMAGFREQ" : imagfreq2, #要計算                                            
    "LST" : lst_list,
    "AZIMUTH" : az_list,
    "ELEVATIO" : el_list,
    "TAU" : tau_list,
    "HUMIDITY" : hum_list,
    "TAMBIENT" : tamb_list,
    "PRESSURE" : press_list,
    "WINDSPEE" : windspee_list,
    "WINDDIRE" : winddire_list,
    "BEAMEFF" : 1, #未使用                                                     
    "RESTFREQ" : obs['restfreq_2'],
    "SIG" : 'T', #未使用                                                       
    "CAL" : 'F', #未使用                                                       
    "SOBSMODE" : sobsmode_list,
    "QUALITY" : 1, #未使用                                                     
    "AOSLEN" : 0.04, #未使用                                                   
    "LOFREQ" : lofreq2, #要計算                                                
    "SYNTH" : 9301.318999999,#要調査[MHz;IF2]2ndLO                             
    "FREQSWAM" : 0,#要調査                                                     
    "COORDSYS" : obs['coordsys'],
    "COSYDEL" : obs['cosydel'],
    "LAMDEL" : obs['lamdel'],
    "BETDEL" : obs['betdel'],
    "OTADEL" : obs['otadel'],
    "OTFVLAM" : 0,
    "OTFVBET" : 0,
    "OTFSCANN" : 0,
    "OTFLEN" : 0,
    "SUBSCAN" : 0, # 要実装                                                    
    "MJD" : mjd_list,
    "SECOFDAY" : secofday_list,
    "SIDEBAND" : obs['lo1st_sb_2'],
    "_2NDSB" : obs['lo2nd_sb_2'],
    "_3RDSB" : obs['lo3rd_sb_2'],
    "_2NDLO" : _2NDLO_list2,#ドップラーシフト込み              
    "_3RDLO" : obs['lo3rd_freq_2'],
    "SUBREF" : subref_list,
    "LOCKSTAT" : 'F'#未使用                                                    
    }


print(_2NDLO_list1)
print(_2NDLO_list2)
f1 = os.path.join(savedir,'n2ps_%s_IF1.fits'%(timestamp))
f2 = os.path.join(savedir,'n2ps_%s_IF2.fits'%(timestamp))
#numpy.save(f1+".npy",read1)
#numpy.save(f2+".npy",read2)

import n2fits_write
n2fits_write.write(read1,f1)
n2fits_write.write(read2,f2)

obs_log.end_script(name, dirname)

