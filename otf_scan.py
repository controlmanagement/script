#! /usr/bin/env python
# coding:utf-8


# Configurations
# ==============
# Info
# ----

name = '_otf_2016'
description = 'Get OTF spectrum'

# Config Parameters
# =================

# Default parameters
# ------------------
obsfile = ''
tau = 0.0
c = 299792458

# Argument handler
# ================

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
import shutil
import time
import numpy
import obs_log
import doppler_nanten
dp = doppler_nanten.doppler_nanten()
import controller
con = controller.controller()
con.dome_track()
import sys
import signal
def handler(num, flame):
    print("!!ctrl+C!!")
    print("STOP MOVING")
    con.tracking_end()
    sys.exit()
signal.signal(signal.SIGINT, handler)

list = []
list.append("--obsfile")
list.append(obsfile)
obs_log.start_script(name, list)



obsdir = '/home/amigos/NECST/script/obslist/otf/'
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
    except:
        try:
            obs[_key] = obs[_value]
        except:
            pass
    if not _value.find('/') == -1 and _value.find('*') == -1:
        _value1,_value2 = _value.split('/',1)
        _value1 = _value1.strip()
        _value2 = _value2.strip()
        if isinstance(_value1,str):
            try:
                _value1 = float(_value1)
            except:
                pass
        else:
            pass
        if isinstance(_value2,str):
            try:
                _value2 = float(_value2)
            except:
                pass
        else:
            pass
        if isinstance(_value1,float) and isinstance(_value2,float):
            obs[_key] = (float(_value1)*100)/(float(_value2)*100)
        elif not isinstance(_value1,float) and not isinstance(_value2,float):
            obs[_key] = (obs[_value1]*100)/(obs[_value2]*100)
        elif isinstance(_value1,float):
            obs[_key] = (float(_value1)*100)/(obs[_value2]*100)
        elif isinstance(_value2,float):
            obs[_key] = (obs[_value1]*100)/(float(_value2)*100)
        else:
            print('Error')
    elif _value.find('/') == -1 and not _value.find('*') == -1:
        _value1,_value2 = _value.split('*',1)
        _value1 = _value1.strip()
        _value2 = _value2.strip()
        if isinstance(_value1,str):
            try:
                _value1 = float(_value1)
            except:
                pass
        if isinstance(_value2,str):
            try:
                _value2 = float(_value2)
            except:
                pass
        if isinstance(_value1,float) and isinstance(_value2,float):
            obs[_key] = (float(_value1)*100)*(float(_value2)*100)/10000
        elif not isinstance(_value1,float) and not isinstance(_value2,float):
            obs[_key] = (obs[_value1]*100)*(obs[_value2]*100)/10000
        elif isinstance(_value1,float):
            obs[_key] = (float(_value1)*100)*(obs[_value2]*100)/10000
        elif isinstance(_value2,float):
            obs[_key] = (obs[_value1]*100)*(float(_value2)*100)/10000
        else:
            print('Error')
    else:
        pass

    continue

integ_on = obs['exposure']
integ_off = obs['exposure_off']
#ra = obs['lambda_on']#on点x座標,l,いらない？
#dec = obs['beta_on']#on点y座標,b,いらない？
offx = obs['lambda_off']#off点x座標
offy = obs['beta_off']#off点y座標

# Initial configurations
# ----------------------

datahome = 'data'
timestamp = time.strftime('%Y%m%d%H%M%S')
dirname = 'n%s_%s_%s_otf_%s'%(timestamp ,obs['molecule_1'] ,obs['transiti_1'].split('=')[1],obs['object'])
savedir = os.path.join(datahome, name, dirname)

print('mkdir {savedir}'.format(**locals()))
os.makedirs(savedir)

# Scan Parameters
# --------------- 
lambda_on = obs['lambda_on']#[deg]
beta_on = obs['beta_on']#[deg]
sx = obs['lamdel_off']+obs['start_pos_x']#[arcsec]
sy = obs['betdel_off']+obs['start_pos_y']#[arcsec]
direction = int(obs['scan_direction'])
scan_coord = []
scan_dos = []
if direction == 0:
    dx = float(obs['otfvel'])*float(obs['exposure'])#[arcsec]
    dy = 0
    gridx = 0
    gridy = obs['grid']#[arcsec]
elif direction ==1:
    dx = 0
    dy = float(obs['otfvel'])*float(obs['exposure'])#[arcsec]
    gridx = obs['grid']#[arcsec]
    gridy = 0
else:
    con.tracking_end()
    print('Error:direction')
    sys.exit()
dt = obs['exposure']#float(obs['grid']/obs['otfvel'])

if obs['otadel'].lower() == 'y':
    offset_dcos = 1
else:
    offset_dcos = 0
if obs['coordsys'].lower() == 'j2000' or obs['coordsys'].lower() == 'b1950':
    coord_sys = 'EQUATORIAL'
elif obs['coordsys'].lower() == 'galactic':
    coord_sys = 'GALACTIC'
else:
    con.tracking_end()
    print('coord_sys:Error')
    sys.exit()
if obs['cosydel'].lower() == 'j2000' or obs['cosydel'].lower() == 'b1950':
    cosydel = 'EQUATORIAL'
elif obs['cosydel'].lower() == 'galactic':
    cosydel = 'GALACTIC'
elif obs['cosydel'].lower() == 'horizontal':
    cosydel = 'HORIZONTAL'
else:
    con.tracking_end()
    print('cosydel:Error')
    sys.exit()
if obs['lo1st_sb_1'] == 'U':#後半に似たのがあるけど気にしない
    sb1 = 1
else:
    sb1 = -1
if obs['lo1st_sb_2'] == 'U':#後半に似たのがあるけど気にしない
    sb2 = 1
else:
    sb2 = -1


lamda = c/float(obs['restfreq_1'])#分光計 1
otflen = obs['otflen']/obs['exposure']
scan_point = float(otflen) #scan_point for 1 line
scan_point = int(scan_point)
rampt = dt*obs['lamp_pixels']
print(scan_point)
#if scan_point > int(scan_point):
    #print("!!ERROR scan number!!")

print('coord_sys = '+coord_sys)
total_count = int(obs['N'])#total scan_line



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
lamdel_list = []
betdel_list = []
subscan_list = []

print('Start experimentation')
print('')

savetime = con.read_status()['Time']

rp = int(obs['nTest'])
rp_num = 0
n = int(total_count)
latest_hottime = 0

# define thread
# ---------------
while rp_num < rp:
    print('repeat : ',rp_num)
    num = 0
    while num < n: 
        print('observation :'+str(num))
        print('tracking start')
        con.tracking_end()
        
        if coord_sys == 'EQUATORIAL':
            con.radec_move(offx, offy, obs['coordsys'],
                           off_x=obs['lamdel_off'], off_y=obs['betdel_off'], 
                           offcoord = cosydel)
        elif coord_sys == 'GALACTIC':
            con.galactic_move(offx, offy,
                              off_x=obs['lamdel_off'], off_y=obs['betdel_off'], 
                              offcoord = cosydel)
        print('moving...')
        while not con.read_track():
            time.sleep(0.1)
            continue

        status = con.read_status()
        dome_az = status['Current_Dome']
        if dome_az < 0.:
            dome_az += 360.
        ant_az = status['Current_Az']
        if ant_az < 0.:
            ant_az += 360.
        while abs(dome_az-ant_az) > 3. and abs(dome_az-ant_az) < 357.:
            time.sleep(0.5)
            status = con.read_status()
            dome_az = status['Current_Dome']
            if dome_az <0.:
                dome_az += 360.
            ant_az = status['Current_Az']
            if ant_az < 0.:
                ant_az += 360.
            continue
        
        


        print('tracking OK')
        _now = time.time()
        if _now > latest_hottime+60*obs['load_interval']:
            print('R')
            con.move_hot('in')
        
            temp = float(con.read_status()['CabinTemp1']) + 273.15
        
            print('Temp: %.2f'%(temp))
            print('get spectrum...')
            dp2 = dp.set_track(obs['lambda_on'], obs['beta_on'], obs['vlsr'], obs['coordsys'], obs['lamdel_off'], obs['betdel_off'], offset_dcos, obs['cosydel'], integ_off*2+integ_on+rampt+(dt*scan_point), obs['restfreq_1']/1000., obs['restfreq_2']/1000., sb1, sb2, 8038.000000000/1000., 9301.318999999/1000.)#SYNTHが固定値の場合
            dp1 = dp.set_track(obs['lambda_on'], obs['beta_on'], obs['vlsr'], obs['coordsys'], obs['lamdel_off'], obs['betdel_off'], offset_dcos, obs['cosydel'], integ_off*2+integ_on+rampt, obs['restfreq_1']/1000., obs['restfreq_2']/1000., sb1, sb2, 8038.000000000/1000., 9301.318999999/1000.)#SYNTHが固定値の場合
            d = con.oneshot(exposure=integ_off)
            d1 = d['dfs1'][0]
            d2 = d['dfs2'][0]
            d1_list.append(d1)
            d2_list.append(d2)
            tdim6_list.append([16384,1,1])
            date_list.append(con.read_status()['Time'])
            thot_list.append(temp)
            vframe_list.append(dp1[0])
            vframe2_list.append(dp2[0]) 
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
            _2NDLO_list1.append(dp1[3]['sg21']*1000)
            _2NDLO_list2.append(dp1[3]['sg22']*1000) 
            lamdel_list.append(0)#
            betdel_list.append(0)#
            subscan_list.append(int(num)+1)
            pass


        else:
            dp2 = dp.set_track(obs['lambda_on'], obs['beta_on'], obs['vlsr'], obs['coordsys'], obs['lamdel_off'], obs['betdel_off'], offset_dcos, obs['cosydel'], integ_off+integ_on+rampt+(dt*scan_point), obs['restfreq_1']/1000., obs['restfreq_2']/1000., sb1, sb2, 8038.000000000/1000., 9301.318999999/1000.)#SYNTHが固定値の場合
            dp1 = dp.set_track(obs['lambda_on'], obs['beta_on'], obs['vlsr'], obs['coordsys'], obs['lamdel_off'], obs['betdel_off'], offset_dcos, obs['cosydel'], integ_off+integ_on+rampt, obs['restfreq_1']/1000., obs['restfreq_2']/1000., sb1, sb2, 8038.000000000/1000., 9301.318999999/1000.)#SYNTHが固定値の場合
            pass

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
        vframe_list.append(dp1[0]) 
        vframe2_list.append(dp2[0]) 
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
        _2NDLO_list1.append(dp1[3]['sg21']*1000)
        _2NDLO_list2.append(dp1[3]['sg22']*1000) 
        lamdel_list.append(0)#
        betdel_list.append(0)#
        subscan_list.append(int(num)+1)

        try:#デバッグ用
            print('move ON')
            con.tracking_end()
            ssx = (sx + num*gridx) - float(dx)/float(dt)*rampt-float(dx)/2.#rampの始まり
            ssy = (sy + num*gridy) - float(dy)/float(dt)*rampt-float(dy)/2.#rampの始まり
            if coord_sys == 'EQUATORIAL':
                con.radec_move(lambda_on, beta_on, obs['coordsys'],
                               off_x = ssx,
                               off_y = ssy,
                               offcoord = cosydel,
                               dcos = offset_dcos)
            elif coord_sys == 'GALACTIC':
                con.galactic_move(lambda_on, beta_on,
                                  off_x= ssx, 
                                  off_y= ssy, 
                                  offcoord = cosydel,
                                  dcos = offset_dcos)

            print('moving...')
            time.sleep(0.001)#分光計の指令値更新を待つ(一応)
            while not con.read_track():#通り過ぎた場合もTrueになるため
                time.sleep(0.001)
                continue
            time.sleep(0.1)
            while not con.read_track():#2回目
                time.sleep(0.001)
                continue
            time.sleep(0.1)
            while not con.read_track():#一応3回目
                time.sleep(0.001)
                continue
            print('reach ramp_start')
            #rampまで移動
            con.tracking_end()# 2つの thread がぶつかるのを防ぐ
            print(' OTF scan_satart!! ')
            print('move ON')
            start_on = con.otf_scan(lambda_on, beta_on, offset_dcos, coord_sys, dx, dy, dt, scan_point, rampt, 0, lamda, 'hosei_230.txt', obs['coordsys'].lower(), off_x = sx + num*gridx, off_y = sy + num*gridy, off_coord = cosydel)
            d = con.oneshot(repeat = scan_point ,exposure = integ_on ,
                            stime = start_on)
            print('getting_data...')

            while start_on + obs['otflen']/24./3600. > 40587 + time.time()/(24.*3600.):
                time.sleep(0.001)

            #とりあえずスキャン中は同じ値
            temp = float(con.read_status()['CabinTemp1']) + 273.15
            date = con.read_status()['Time']
            lst = con.read_status()['LST']
            az = con.read_status()['Current_Az']
            el = con.read_status()['Current_El']
            hum = con.read_status()['OutHumi']
            tamb = con.read_status()['OutTemp']
            press = con.read_status()['Press']
            windspee = con.read_status()['WindSp']
            winddire = con.read_status()['WindDir']
            mjd = con.read_status()['MJD']
            sec = con.read_status()['Secofday']
            subref = con.read_status()['Current_M2']

            _on = 0
            while _on < scan_point:
                print(_on+1)
                d1 = d['dfs1'][_on]
                d2 = d['dfs2'][_on]
                d1_list.append(d1)
                d2_list.append(d2)
                lamdel_on = round((sx + num*gridx) + dx*_on,0)
                betdel_on = round((sy + num*gridy) + dy*_on,0)
                tdim6_list.append([16384,1,1])
                date_list.append(date)
                thot_list.append(temp)
                vframe_list.append(dp1[0]) 
                vframe2_list.append(dp2[0]) 
                lst_list.append(lst)
                az_list.append(az)
                el_list.append(el)
                tau_list.append(tau)
                hum_list.append(hum)
                tamb_list.append(tamb)
                press_list.append(press)
                windspee_list.append(windspee)
                winddire_list.append(winddire)
                sobsmode_list.append('ON')
                mjd_list.append(mjd)
                secofday_list.append(sec)
                subref_list.append(subref)
                tsys_list.append(tsys)
                _2NDLO_list1.append(dp1[3]['sg21']*1000)
                _2NDLO_list2.append(dp1[3]['sg22']*1000)
                lamdel_list.append(lamdel_on)
                betdel_list.append(betdel_on)
                subscan_list.append(int(num)+1)
                _on += 1

            print('stop')
            con.tracking_end()

        except Exception as e:
            con.tracking_end()
            print('Error : loop')
            print(e)
            sys.exit()
        num += 1
        continue
    rp_num += 1
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
vframe_list.append(dp1[0])
vframe2_list.append(dp2[0])
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
_2NDLO_list1.append(dp1[3]['sg21']*1000)
_2NDLO_list2.append(dp1[3]['sg22']*1000)
lamdel_list.append(0)
betdel_list.append(0)
subscan_list.append(int(num)+1)
con.move_hot('out')

print('observation end')
con.tracking_end()

#Other_list_data
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
cdelt1_1 = (-1)*ul1*0.079370340319607024 #[(km/s)/ch]
#dv1 = (c*cdelt1_1)/obs['restfreq_1']
crpix1_1 = 8191.5 - obs['vlsr']/cdelt1_1 - (500-obs['if3rd_freq_1'])/0.061038881767686015


if obs['lo1st_sb_2'] == 'U':
    ul = 1
else:
    ul = -1
imagfreq2 = obs['obsfreq_2'] - ul*obs['if1st_freq_2']*2
lofreq2 = obs['obsfreq_2'] - ul*obs['if1st_freq_2']*1

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
cdelt1_2 = (-1)*ul2*0.0830267951512371 #[(km/s)/ch]                           
#dv2 = (c*cdelt1_2)/obs['restfreq_2']
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
    "LAMDEL" : lamdel_list,#arcsec
    "BETDEL" : betdel_list,#arcsec
    "OTADEL" : obs['otadel'],
    "OTFVLAM" : 0,#要検討
    "OTFVBET" : 0,#要検討
    "OTFSCANN" : obs['N'],
    "OTFLEN" : obs['otflen'],
    "SUBSCAN" : subscan_list,
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


#d2list                                                                        
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
    "LAMDEL" : lamdel_list,#arcsec
    "BETDEL" : betdel_list,#arcsec
    "OTADEL" : obs['otadel'],
    "OTFVLAM" : 0,#要検討
    "OTFVBET" : 0,#要検討
    "OTFSCANN" : obs['N'],
    "OTFLEN" : obs['otflen'],
    "SUBSCAN" : subscan_list,                                                  
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

con.tracking_end()
#改築予定地
#f1 = os.path.join(savedir,'n2line_otf_%s_IF1.fits'%(timestamp))
f1 = os.path.join(savedir,'n%s_%s_%s_otf_%s.fits'%(timestamp ,obs['molecule_1'],obs['transiti_1'].split('=')[1],obs['object']))
#f2 = os.path.join(savedir,'n2line_otf_%s_IF2.fits'%(timestamp))
f2 = os.path.join(savedir,'n%s_%s_%s_otf_%s.fits'%(timestamp ,obs['molecule_2'],obs['transiti_2'].split('=')[1],obs['object']))
#numpy.save(f1+".npy",read1)
#numpy.save(f2+".npy",read2)

print('dp1 : ',dp1)
print('VFRAME1 : ',dp1[0])
print('2ndLO1_1 : ',dp1[3]['sg21']*1000)
print('2ndLO1_2 : ',dp1[3]['sg22']*1000)
print('dp2 : ',dp2)
print('VFRAME2 : ',dp2[0])
print('2ndLO2_1 : ',dp2[3]['sg21']*1000)
print('2ndLO2_2 : ',dp2[3]['sg22']*1000)

import n2fits_write
n2fits_write.write(read1,f1)
n2fits_write.write(read2,f2)

shutil.copy("/home/amigos/NECST/soft/server/hosei_230.txt", savedir+"/hosei_copy")
obs_log.end_script(name, dirname)

