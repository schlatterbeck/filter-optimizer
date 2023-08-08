#!/usr/bin/python3

import sys
import os
from csv import DictWriter

fields = \
    ( 'variant'
    , 'prefilter'
    , 'cross'
    , 'Cr'
    , 'dither'
    , 'dither_p_i'
    , 'jitter'
    , 'np'
    , 'F'
    , 'F_dec'
    , 'sort'
    , 'randseed'
    , 'eval'
    , 'neval'
    , 'iter'
    )
dw = DictWriter (sys.stdout, delimiter = ';', fieldnames = fields)
dw.writerow (dict ((f, f) for f in fields))

    # name of option               name in csv,  lookup if bool
options = dict \
    ( crossover_rate            = ('Cr',         ())
    , de_variant                = ('variant',    ())
    , dither                    = ('dither',     ())
    , dither_per_individual     = ('dither_p_i', ('0',      '1'))
    , jitter                    = ('jitter',     ())
    , popsize                   = ('np',         ())
    , random_seed               = ('randseed',   ())
    , scale_factor              = ('F',          ())
    , scale_with_popsize        = ('F_dec',      ())
    , sort_population           = ('sort',       ('0',      '1'))
    , use_exponential_crossover = ('cross',      ('bin',    'exp'))
    , use_prefilter             = ('prefilter',  ('0',      '1'))
    )

def main (argv = sys.argv [1:]):
    for fn in argv:
        n, e = os.path.splitext (fn)
        params = n.split ('-')
        d = {}
        # Params encoded in filename
        if len (params) > 4:
            d ['variant'] = params [1]
            d ['cross']   = params [2]
            d ['np']      = params [3]
            d ['F']       = params [4].lstrip ('F')
            offs          = 6
            if params [5].endswith ('sort'):
                offs     = 5
                d ['Cr'] = 1.0
            else:
                d ['Cr'] = params [5]
            d ['sort']     = str (int (params [offs] == 'sort'))
            d ['randseed'] = params [offs+1]
            if not srt:
                assert params [5] == 'nosort'
        with open (fn, 'r') as f:
            found = False
            for line in f:
                if line.startswith ('The Best Evaluation:'):
                    found      = True
                    d ['eval'] = line.split (':', 1) [1].strip ().rstrip ('.')
                    continue
                if found:
                    if line.startswith ('#'):
                        dw.writerow (d)
                        found = False
                        continue
                    if line.startswith ('Iter:'):
                        try:
                            t, v1, t2, v2 = line.split ()
                        except ValueError:
                            t, v1, t2, v2, t3, v3 = line.split ()
                        d ['iter']   = v1
                        d ['neval']  = v2
                        continue
                    try:
                        k, v = (x.strip () for x in line.split (':', 1))
                    except ValueError:
                        # Should not happen
                        continue
                    if k in options:
                        key, boolconv = options [k]
                        if boolconv:
                            if v == 'True':
                                d [key] = boolconv [1]
                            else:
                                d [key] = boolconv [0]
                        else:
                            d [key] = v
# end def main
