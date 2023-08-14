#!/usr/bin/python3

import sys
from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
from argparse import ArgumentParser
from . import filterplot

class Experiment:

    def __init__ \
        ( self, nzeros, npoles, gene
        , title = None, is_valid = True, a0 = 0.00390625, prefilter = False
        , mag_l = None, mag_u = None, del_l = None, del_u = None
        ):
        self.nzeros      = nzeros
        self.npoles      = npoles
        self.gene        = gene
        self.title       = title
        self.is_valid    = is_valid
        self.a0          = a0
        self.prefilter   = prefilter
        self.mag_l       = mag_l
        self.mag_u       = mag_u
        self.del_l       = del_l
        self.del_u       = del_u
        if not (mag_l or mag_u or del_l or del_u):
            self.mag_l = filterplot.default_lower_magnitude.copy ()
            self.mag_u = filterplot.default_upper_magnitude.copy ()
            self.del_l = filterplot.default_lower_delay.copy ()
            self.del_u = filterplot.default_upper_delay.copy ()
        rz = range (0, 2 * nzeros, 2)
        rp = range (0, 2 * npoles, 2)
        zeros = [ gene [k]          * np.e ** (2j * np.pi
                * gene [k+1])          for k in rz
                ]
        poles = [ gene [k+2*nzeros] * np.e ** (2j * np.pi
                * gene [k+2*nzeros+1]) for k in rp
                ]
        self.zeros = zeros
        self.poles = poles
        filterplot.update_conjugate_complex (self.zeros)
        filterplot.update_conjugate_complex (self.poles)
        self.b, self.a = signal.zpk2tf (zeros, poles, self.a0)
    # end def __init__

    @classmethod
    def Parse (cls, f):
        nzeros = 5
        npoles = 4
        best = 'The Best Evaluation:'
        gene = []
        n = None
        mag_l = mag_u = del_l = del_u = ''
        prefilter   = False
        scale_by_pi = True
        title       = None
        for line in f:
            line = line.strip ()
            if line.startswith (best):
                line = line.rstrip ('.')
                eval = float (line.split (':') [-1])
                n = 0
                continue
            if n is not None:
                if line.startswith ('Iter:'):
                    title = line
                if line.startswith ('magnitude_lower_bound'):
                    mag_l = line.split (':')[-1]
                if line.startswith ('magnitude_upper_bound'):
                    mag_u = line.split (':')[-1]
                if line.startswith ('delay_lower_bound'):
                    del_l = line.split (':')[-1]
                if line.startswith ('delay_upper_bound'):
                    del_u = line.split (':')[-1]
                if line.startswith ('use_prefilter'):
                    if line.split (':')[-1].strip () == 'True':
                        prefilter = True
                if line.startswith ('scale_by_pi'):
                    if line.split (':')[-1].strip () == 'False':
                        scale_by_pi = False
                if line.startswith ('poles'):
                    npoles = int (line.split (':')[-1])
                if line.startswith ('zeros'):
                    nzeros = int (line.split (':')[-1])
                if line.startswith ('#'):
                    k, r = line [1:].split (':')
                    assert int (k) == n
                    g = [x.strip().lstrip('[').rstrip(']')
                         for x in r.split (',')
                        ]
                    g = [float (x) for x in g]
                    gene.extend (g)
                    n += len (g)
                elif n > 0:
                    break
        if gene:
            mag_l = filterplot.Filter_Bounds.Parse \
                (mag_l, scale_by_pi = scale_by_pi, is_lower = True)
            mag_u = filterplot.Filter_Bounds.Parse \
                (mag_u, scale_by_pi = scale_by_pi)
            del_l = filterplot.Filter_Bounds.Parse \
                (del_l, scale_by_pi = scale_by_pi, is_lower = True)
            del_u = filterplot.Filter_Bounds.Parse \
                (del_u, scale_by_pi = scale_by_pi)
            return cls \
                ( nzeros, npoles, gene
                , title = title, is_valid = eval == 0, prefilter = prefilter
                , mag_l = mag_l, mag_u = mag_u, del_l = del_l, del_u = del_u
                )
    # end def Parse

    def display (self, fine = False, **kw):
        w, h = signal.freqz (self.b, self.a, 50000)
        r = np.arange (0, np.pi, np.pi / 512)
        r = np.array (sorted (np.concatenate ((r, self.del_u.x))))
        (wgd, gd) = signal.group_delay ((self.b, self.a), r)
        if self.prefilter:
            # Pre-Filter, only makes sense for original example
            fir  = \
                [ -0.033271, -0.019816,  0.169865,  0.415454
                ,  0.415454,  0.169865, -0.019816, -0.033271
                ]
            fir_w, fir_h = signal.freqz (fir, [1.0], 50000)
            h = fir_h * h
            t = 'Experiment with pre-filter'
        else:
            t = 'Experiment without pre-filter'
        if self.title:
            t = t + '\n' + self.title
        d = dict (fs = 1.0, title = t, bounds = [self.mag_l, self.mag_u])
        if kw.get ('scale_rad', None):
            d.update (fs = None)
        if kw.get ('frequency', None):
            d.update (fs = kw ['frequency'])
        d.update (scatter = kw.get ('scatter', None))
        if fine:
            filterplot.plot_response \
                (w, h, xmax = 0.4,  ymax = 0.1, ymin = -0.1, **d)
            filterplot.plot_response \
                (w, h, xmin = 0.25, ymax = -5, **d)
        else:
            filterplot.plot_response (w, h, **d)
        d.update (auto_ylimit = kw.get ('auto_ylimit'))
        d ['bounds'] = [self.del_l, self.del_u]
        filterplot.plot_delay (wgd, gd, **d)
        filterplot.pole_zero_plot (self.poles, self.zeros)
    # end def display
# end class Experiment

def main (argv = sys.argv [1:]):
    cmd = ArgumentParser ()
    cmd.add_argument \
        ( 'filename'
        , help    = 'File to parse, can contain multiple experiments'
        , nargs   = '+'
        )
    cmd.add_argument \
        ( '--dont-use-filename-as-title'
        , help    = "Use internal parameters in file as title"
        , dest    = 'filename_as_title'
        , default = True
        , action  = 'store_false'
        )
    cmd.add_argument \
        ( '-f', '--frequency'
        , help    = "Sampling frequency for X-axis, overrides --scale-rad"
        , type    = float
        )
    cmd.add_argument \
        ( '--no-auto-ylimit'
        , help    = "Do not auto-limit the delay plot on Y-axis"
        , dest    = 'auto_ylimit'
        , default = True
        , action  = 'store_false'
        )
    cmd.add_argument \
        ( '--scale-rad'
        , help    = "Scale X by radians"
        , default = False
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '--scatter'
        , help    = "Plot as scatter plot not line"
        , default = False
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '--show-failed'
        , help    = "Show experiments that didn't find a solution"
        , default = False
        , action  = 'store_true'
        )
    args = cmd.parse_args ()
    for fn in args.filename:
        with open (fn, 'r') as f:
            while 1:
                ex = Experiment.Parse (f)
                if ex is None:
                    break
                if args.filename_as_title:
                    ex.title = fn
                if ex.is_valid or args.show_failed:
                    ex.display (**vars (args))
# end def main

if __name__ == '__main__':
    main ()
