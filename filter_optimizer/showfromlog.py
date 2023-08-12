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
        , as_samples = False
        , mag_l = None, mag_u = None, del_l = None, del_u = None
        ):
        self.nzeros      = nzeros
        self.npoles      = npoles
        self.gene        = gene
        self.title       = title
        self.is_valid    = is_valid
        self.a0          = a0
        self.prefilter   = prefilter
        self.as_samples  = as_samples
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
        zeros = [gene [k]    * np.e ** (2j * np.pi * gene [k+1])  for k in rz]
        poles = [gene [k+10] * np.e ** (2j * np.pi * gene [k+11]) for k in rp]
        self.zeros = zeros
        self.poles = poles
    # end def __init__

    @classmethod
    def Parse (cls, f, as_samples = False):
        nzeros = 5
        npoles = 4
        best = 'The Best Evaluation:'
        gene = []
        n = None
        mag_l = mag_u = del_l = del_u = ''
        prefilter   = False
        scale_by_pi = True
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
                , as_samples = as_samples
                , mag_l = mag_l, mag_u = mag_u, del_l = del_l, del_u = del_u
                )
    # end def Parse

    def display (self):
        filterplot.update_conjugate_complex (self.zeros)
        filterplot.update_conjugate_complex (self.poles)
        (b, a) = signal.zpk2tf (self.zeros, self.poles, self.a0)
        (w, h) = signal.freqz  (b, a, 50000)
        (wgd, gd) = signal.group_delay ((b, a))
        if self.prefilter:
            t = 'Experiment with pre-filter'
        else:
            t = 'Experiment without pre-filter'
        if self.title:
            t = t + '\n' + self.title
        d = dict (fs = 1.0, title = t, bounds = [self.mag_l, self.mag_u])
        filterplot.plot_response (w, h, **d)
        #filterplot.plot_response \
        #    (w, h, xmax = 0.4,  ymax = 0.1, ymin = -0.1, **d)
        #filterplot.plot_response \
        #    (w, h, xmin = 0.25, ymax = -5, **d)
        d ['bounds'] = [self.del_l, self.del_u]
        if self.as_samples:
            d.update (as_samples = True)
        filterplot.plot_delay (wgd, gd, xmax = 0.35, **d)
        filterplot.pole_zero_plot (self.poles, self.zeros)
    # end def display
# end class Experiment

def main (argv = sys.argv [1:]):
    cmd = ArgumentParser ()
    cmd.add_argument \
        ( 'filename'
        , help    = 'File to parse, can contain multiple experiments'
        )
    cmd.add_argument \
        ( '--show-failed'
        , help    = "Show experiments that didn't find a solution"
        , default = False
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '--as-samples'
        , help    = "Show delay in units of samples (not rad)"
        , default = False
        , action  = 'store_true'
        )
    args = cmd.parse_args ()
    with open (args.filename, 'r') as f:
        while 1:
            ex = Experiment.Parse (f, as_samples = args.as_samples)
            if ex is None:
                break
            if ex.is_valid or args.show_failed:
                ex.display ()
# end def main

if __name__ == '__main__':
    main ()
