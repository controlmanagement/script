#  -------- please select standard source parameter -----

OBJECT = 'OriKL'
ON_X = 83.806
ON_Y = -5.374
ON_COORD = 'J2000'
OFF_NAME = 'OriKL'
OFF_X = 82.559
OFF_Y = -5.668
DATA_PATH = '/home/amigos/NECST/data/ps/'

params={}
#==========================
params['object'] = OBJECT
params['on_x'] = ON_X
params['on_y'] = ON_Y
params['on_coord'] = ON_COORD
params['off_name'] = OFF_NAME
params['path'] = DATA_PATH
params['offset_on_x'] = 0.0
params['offset_on_y'] = 0.0
params['offset_on_dcos'] = 0
params['offset_on_coord'] = 'HORIZONTAL'
params['repeat'] = 1
params['exposure'] = 20.0
params['r_interval'] = 10.0
params['hosei'] = '/home/amigos/NECST/soft/server/hosei_230.txt'

params['planet'] = None

import core.observer

obs = core.observer.observer()
obs.operate_ps(params)
