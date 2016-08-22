#! /usr/bin/env python
# coding:utf-8


# Configurations
# ==============
# Info
# ----

name = 'radio_pointing_line_9'
description = 'Do radio pointing'


# Default parameters
# ------------------
obsfile = ''
tau = 0.0


# Argument handler
# ================

import argparse

p = argparse.ArgumentParser(description=description)
p.add_argument('--obsfile', type=str,
               help='absolute path for obsfile', required=True)
p.add_argument('--tau', type=float,
               help='tau. default=%.1f'%(tau))

args = p.parse_args()

if args.obsfile is not None: obsfile = args.obsfile
if args.tau is not None: tau = args.tau

# Main
# ====
import os
import sys
import time
import signal
import numpy

tstmp = time.strftime("%H%M%S")
daystmp = time.strftime("%Y%m%d")
f = open("./data/obs_log/"+daystmp+".txt", "a")
f.write(tstmp+" radio_pointing.py "+obsfile+"\n")
f.close()

obs_items = open(obsfile, 'r').read().split('\n')
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
    #except NameError:
    except:
        try:
            obs[_key] = eval(_value, obs)
        except:
            obs[_key] = obs[_value]
            pass
    continue

integ = obs['exposure']
ra = obs['lambda_on']#on点x座標
dec = obs['beta_on']#on点y座標
offx = obs['lambda_off']#off点x座標
offy = obs['beta_off']#off点y座標
xgrid = obs["xgrid"] #offset of pointing(x)
ygrid = obs["ygrid"] #offset of pointing(y)
point_n = obs["N"] #number of pointing
point_n = int(point_n / 2) + 1 #number of 1line


import controller
con = controller.controller()


def handler(num, flame):
    con.tracking_end()
    print("!!ctrl + c!!")
    print("Stop antenna")
    sys.exit()

signal.signal(signal.SIGINT, handler)

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


print('Start pointing')
print('')

savetime = con.read_status()['Time']
num = 0
n = int(obs['nTest']) * 2
latest_hottime = 0


#for debug
print("xgrid:"+str(xgrid))
print("ygrid:"+str(ygrid))
print("n:"+str(n))
print("point_n:"+str(point_n))



while num < n:
    p_n = 0
    while p_n < point_n:
        ra = obs['lambda_on']
        dec = obs['beta_on']
        
        
        print("num "+str(num))
        print("p_n "+str(p_n))
        
        
        if num % 2 == 1:
            ra += xgrid / 3600. * (p_n - (int(point_n/2)))
        else:
            dec += ygrid / 3600. * (p_n - (int(point_n/2)))
        
        
        
        print("ra:"+str(ra))
        print("dec:"+str(dec))
        
        
        
        print('observation :'+str(num))
        print('tracking start')
        con.tracking_end()
        con.radec_move(ra, dec, obs['coordsys'], off_x=offx, off_y=offy)
        print('moving...')
        while not con.read_track():
            time.sleep(0.1)
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
        p_n += 1
        
        print('tracking OK')
        _now = time.time()
        if _now > latest_hottime+60*obs['load_interval']:
            print('R')
            con.move_hot('in')
            
            temp = float(con.read_status()['CabinTemp1']) + 273.15
            
            print('Temp: %.2f'%(temp))
            
            print('get spectrum...')
            d = con.oneshot(exposure=integ)
            d1 = d['dfs1'][0]
            d2 = d['dfs2'][0]
            d1_list.append(d1)
            d2_list.append(d2)
            tdim6_list.append([16384,1,1])
            date_list.append(con.read_status()['Time'])
            thot_list.append(temp)
            vframe_list.append(0)
            vframe2_list.append(0)
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
            pass
        
        
        print('OFF')
        con.move_hot('out')
        con.radec_move(offx, offy, obs['coordsys'])
        
        while not con.read_track():
            time.sleep(0.1)
            continue
        print('tracking OK')
        
        
        print('get spectrum...')
        temp = float(con.read_status()['CabinTemp1']) + 273.15
        d = con.oneshot(exposure=integ)
        d1 = d['dfs1'][0]
        d2 = d['dfs2'][0]
        d1_list.append(d1)
        d2_list.append(d2)
        tdim6_list.append([16384,1,1])
        date_list.append(con.read_status()['Time'])
        thot_list.append(temp)
        vframe_list.append(0)
        vframe2_list.append(0)
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
        
        
        print('move ON')
        con.tracking_end()
        
        con.radec_move(ra, dec, obs['coordsys'])
        
        while not con.read_track():
            time.sleep(0.1)
            continue
        print('tracking OK')
        
        print('ON')     
        
        print('get spectrum...')
        temp = float(con.read_status()['CabinTemp1']) + 273.15
        d = con.oneshot(exposure=integ)
        d1 = d['dfs1'][0]
        d2 = d['dfs2'][0]
        d1_list.append(d1)
        d2_list.append(d2)
        tdim6_list.append([16384,1,1])
        date_list.append(con.read_status()['Time'])
        thot_list.append(temp)
        vframe_list.append(0)
        vframe2_list.append(0)
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
            
            
        print('stop')
        con.tracking_end()
            
    num += 1


print("====test======")
print("num:"+str(num))
print("p_n:"+str(p_n))



#???
d1_list = numpy.array(d1_list)
d2_list = numpy.array(d2_list)
tdim6_list = numpy.array(tdim6_list)
date_list = numpy.array(date_list)
tsys_list = numpy.array(tsys_list)
thot_list = numpy.array(thot_list)
vframe_list = numpy.array(vframe_list)
vframe2_list = numpy.array(vframe2_list)
lst_list = numpy.array(lst_list)
az_list = numpy.array(az_list)
el_list = numpy.array(el_list)
tau_list = numpy.array(tau_list)
hum_list = numpy.array(hum_list)
tamb_list = numpy.array(tamb_list)
press_list = numpy.array(press_list)
windspee_list = numpy.array(windspee_list)
winddire_list = numpy.array(winddire_list)
sobsmode_list = numpy.array(sobsmode_list)
mjd_list = numpy.array(mjd_list)
secofday_list = numpy.array(secofday_list)
subref_list = numpy.array(subref_list)

if obs['lo1st_sb_1'] == 'U':
    ul = -1
else:
    ul = +1
imagfreq1 = obs['obsfreq_1'] + ul*obs['if1st_freq_1']*2  
lofreq1 = obs['obsfreq_1'] + ul*obs['if1st_freq_1']*1

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
cdelt1 = ul1*0.079370340319607024 #(km/s)

dv1 = (300000*cdelt1)/obs['restfreq_1']
crpix1 = 8191.5 - obs['vlsr']/dv1 - (500-obs['if3rd_freq_1'])/cdelt1


if obs['lo1st_sb_2'] == 'U':
    ul = -1
else:
    ul = +1
imagfreq2 = obs['obsfreq_2'] + ul*obs['if1st_freq_2']*2
lofreq2 = obs['obsfreq_2'] + ul*obs['if1st_freq_2']*1

if obs['lo1st_sb_1'] == 'U':
    ul2_1 = +1
else:
    ul2_1 = -1
if obs['lo2nd_sb_1'] == 'U':
    ul2_2 = +1
else:
    ul2_2 = -1
if obs['lo3rd_sb_1'] == 'U':
    ul2_3 = +1
else:
    ul2_3 = -1
ul2 = ul2_1 * ul2_2 * ul2_3
cdelt2 = ul1*0.079370340319607024 #(km/s)                                      

dv2 = (300000*cdelt2)/obs['restfreq_2']
crpix2 = 8191.5 - obs['vlsr']/dv2 - (500-obs['if3rd_freq_2'])/cdelt2

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
    "CRPIX1" : crpix1, #デバイスファイルに追加
    "CDELT1" : cdelt1, #デバイスファイルに追加
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
    "LAMDEL" : 0,
    "BETDEL" : 0,
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
    "_2NDLO" : 8038.000000000,#要調査['SYNTH']
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
    "CRPIX1" : crpix2, #デバイスファイルに追加
    "CDELT1" : cdelt2, #デバイスファイルに追加
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
    "LAMDEL" : 0,
    "BETDEL" : 0,
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
    "_2NDLO" : 8038.000000000,#要調査['SYNTH']                                  
    "_3RDLO" : obs['lo3rd_freq_2'],
    "SUBREF" : subref_list,
    "LOCKSTAT" : 'F'#未使用                                                    
    }



f1 = os.path.join(savedir,'n2ps_%s_IF1.fits'%(timestamp))
f2 = os.path.join(savedir,'n2ps_%s_IF2.fits'%(timestamp))

import n2fits_write
n2fits_write.write(read1,f1)
n2fits_write.write(read2,f2)


