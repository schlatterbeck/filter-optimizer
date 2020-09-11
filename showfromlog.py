#!/usr/bin/python3

import sys
from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
import filterplot

constraints_mag_u = \
    [ [0,    0.04938, 0.2716, 0.2716,  0.3334,  0.3334,   0.395,  0.395,   0.5]
    , [0.01, 0.025,   0.025,  0.05,    0.05,  -12.,     -12.,   -40.,    -40.]
    ]
constraints_mag_l = \
    [ [0,      0.04938, 0.2716, 0.2716, 0.284]
    , [-0.01, -0.025,  -0.025, -0.05,  -0.05]
    ]
constr_filt_u = \
    [ [0, 0.284]
    , np.array ([0.10125, 0.30375]) * 2 * np.pi
    ]
constr_filt_l = \
    [ [0, 0.284]
    , np.array ([-0.10125, -0.30375]) * 2 * np.pi
    ]
constr_delay = [constr_filt_u, constr_filt_l]
constr_magn  = [constraints_mag_u, constraints_mag_l]
a0 = 0.00390625

def display (gene, title = '') :
    rz = range (0, 10, 2)
    rp = range (0,  8, 2)
    zeros = [gene [k]    * np.e ** (2j * np.pi * gene [k+1])  for k in rz]
    poles = [gene [k+10] * np.e ** (2j * np.pi * gene [k+11]) for k in rp]
    filterplot.update_conjugate_complex (zeros)
    filterplot.update_conjugate_complex (poles)
    (b, a) = signal.zpk2tf (zeros, poles, a0)
    (w, h) = signal.freqz  (b, a, 50000)
    (wgd, gd) = signal.group_delay ((b, a))
    t = 'own experiment with pre-filter'
    if title :
        t = t + '\n' + title
    d = dict (fs = 1.0, title = t, constraints = constr_magn)
    #filterplot.plot_response (w, h, **d)
    filterplot.plot_response (w, h, xmax = 0.4,  ymax = 0.1, ymin = -0.1, **d)
    filterplot.plot_response (w, h, xmin = 0.25, ymax = -5, **d)
    d ['constraints'] = constr_delay
    filterplot.plot_delay (wgd, gd, xmax = 0.35, **d)
# end def display

best = 'The Best Evaluation: 0.000000e+00.'
n = None
gene = []
with open (sys.argv [1], 'r') as f :
    for line in f :
        line = line.strip ()
        if line == best :
            n = 0
            continue
        if n is not None :
            if line.startswith ('Iter:') :
                title = line
            if line.startswith ('#') :
                k, r = line [1:].split (':')
                assert int (k) == n
                g = [x.strip().lstrip('[').rstrip(']') for x in r.split (',')]
                g = [float (x) for x in g]
                gene.extend (g)
                n += len (g)
            elif n > 0 :
                d = {}
                if title :
                    d ['title'] = title
                display (gene, **d)
                gene  = []
                n     = None
                title = None
