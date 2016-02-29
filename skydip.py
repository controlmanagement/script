a#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

# -------



EL = [20.,24.,30.,45.,90.]
#EL = [80.,90.]
EXPOSURE = 2.



# -------

import core.observer

obs = core.observer.observer()

params={}
params['elevation'] = EL
params['exposure'] = EXPOSURE
params['path'] = '/home/amigos/maruyama/NANTEN2/data/Qlook/skydip'

obs.operate_skydip(params)
