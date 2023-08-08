#!/usr/bin/python3

import sys
import matplotlib.pyplot as plt
import numpy as np
from csv      import DictReader
from math     import sqrt
from argparse import ArgumentParser
from numbers  import Number

legend = dict.fromkeys \
    (('np', 'cross', 'Cr', 'dither'))

class Eval_Data:

    def __init__ (self, args):
        self.args = args
        result_by_key = {}
        with open (args.filename, 'r')  as f:
            dr = DictReader (f, delimiter = ';')
            if 'randseed' in dr.fieldnames:
                key_attributes = dr.fieldnames [:-4]
            else:
                key_attributes = dr.fieldnames [:5]
                if dr.fieldnames [5] == 'Cr':
                    key_attributes = dr.fieldnames [:6]
            x_axis = None
            self.x_idx = None
            keys = []
            for i, name in enumerate (key_attributes):
                arg = getattr (args, name)
                if  (  arg is None
                    or arg == ''
                    or isinstance (arg, Number) and arg < 0
                    ):
                    if x_axis is None:
                        x_axis = name
                        self.x_idx  = i
                        self.x_name = name
                    else:
                        raise ValueError \
                            ('(More than) two key attributes used for X: %s, %s'
                            % (name, self.x_name)
                            )
                else:
                    keys.append (name)
            if 'Cr' not in keys and self.x_name != 'Cr':
                keys.append ('Cr')
            if 'prefilter' not in keys and self.x_name != 'prefilter':
                keys.append ('prefilter')
            if 'jitter' not in keys and self.x_name != 'jitter':
                keys.append ('jitter')
            if 'dither' not in keys and self.x_name != 'dither':
                keys.append ('dither')
            self.keys = keys = tuple (keys)
            print \
                ( "Trying to match: %s"
                % (', '.join ('%s: %s' % (k, getattr (self.args, k))
                   for k in keys)
                  )
                )
            for rec in dr: 
                rec ['np']    = int (rec ['np'])
                rec ['F']     = float (rec ['F'])
                rec ['sort']  = int (rec ['sort'])
                if 'randseed' in rec:
                    rec ['randseed'] = int (rec ['randseed'])
                else:
                    rec ['randseed'] = int (rec ['idx'])
                    del rec ['idx']
                rec ['eval']  = float (rec ['eval'])
                rec ['neval'] = int (rec ['neval'])
                rec ['iter']  = int (rec ['iter'])
                if 'Cr' in rec:
                    rec ['Cr'] = float (rec ['Cr'])
                else:
                    rec ['Cr'] = 1.0
                # Default for all measurements stored without this info
                if 'prefilter' in rec:
                    rec ['prefilter'] = int (rec ['prefilter'])
                else:
                    rec ['prefilter'] = self.args.prefilter
                if 'dither' in rec:
                    rec ['dither'] = float (rec ['dither'])
                else:
                    rec ['dither'] = self.args.dither
                if 'jitter' in rec:
                    rec ['jitter'] = float (rec ['jitter'])
                else:
                    rec ['jitter'] = self.args.jitter
                if 'F_dec' in rec:
                    rec ['F_dec'] = float (rec ['F_dec'])
                else:
                    rec ['F_dec'] = self.args.F_dec

                do_continue = False
                for k in keys:
                    arg = getattr (args, k)
                    if arg and arg != rec [k]:
                        do_continue = True
                        break
                if do_continue:
                    continue
                key = tuple (rec [k] for k in key_attributes)
                if key not in result_by_key:
                    result_by_key [key] = dict \
                        ( success = 0
                        , fail    = 0
                        , eval    = []
                        , neval   = []
                        )
                if rec ['eval'] == 0:
                    result_by_key [key]['success'] += 1
                    result_by_key [key]['neval'].append (rec ['neval'])
                else:
                    result_by_key [key]['fail'] += 1
                    result_by_key [key]['eval'].append (rec ['eval'])
        for k in result_by_key:
            r = result_by_key [k]
            r ['eval']  = np.array (r ['eval'])
            r ['neval'] = np.array (r ['neval'])
            n = r ['success']
            if n:
                r ['mean'] = sum (r ['neval']) / n
                r ['stdd'] = sqrt (sum ((r ['neval'] - r ['mean']) ** 2)) / n
        self.result_by_key = result_by_key
        if not self.result_by_key:
            raise ValueError ("No results found")
    # end def __init__

    def plot_eval_success (self):
        rbk  = self.result_by_key
        fig  = plt.figure ()
        ax1  = fig.add_subplot (111)
        x    = []
        y1   = []
        y2   = []
        yerr = []
        nev  = []
        xmin = 1e6
        xmax = -1
        for k in sorted (rbk, key = lambda x: x [self.x_idx]):
            r = rbk [k]
            a = k [self.x_idx]
            x.append (a)
            if a < xmin:
                xmin = a
            if a > xmax:
                xmax = a
            y2.append ((r ['success']) / (r ['success'] + r ['fail']) * 100)
            if r ['success']:
                y1.append (r ['mean'])
                nev.append (r ['neval'])
            else:
                y1.append (0)
                nev.append (np.array ([]))
        nev = np.array (nev)

        plt.title \
            ( 'Evaluations, Successes\n'
            + ' '.join
                ( '='.join ((k, str (getattr (self.args, k))))
                  for k in self.keys if k in legend
                )
            )
        plt.xlabel (self.x_name)
        tick = (xmax - xmin) / len (x) / 2.
        ml   = 0
        for r in nev:
            if ml < len (r):
                ml = len (r)
        if ml:
            if len (x) == 1:
                bp = ax1.boxplot (nev [0] / 1000, positions = x)
            else:
                bp = ax1.boxplot (nev / 1000, positions = x, widths = tick)
            plt.ylabel \
                ('Evals (thousands)', color = bp ['medians'][0].get_color ())
        ax1.set_xlim (xmin - tick / 2, xmax + tick / 2, auto = True)
        ax2 = ax1.twinx ()
        if len (x) == 1:
            p, = ax2.plot   (x, y2, 'o', markersize = 5)
        else:
            p, = ax2.plot   (x, y2)
        plt.ylabel ('Successes (%)', color = p.get_color ())
        plt.show ()
    # end def plot_eval_success

# end class Eval_Data

def main ():
    cmd = ArgumentParser ()
    cmd.add_argument \
        ( 'filename'
        , help    = "File name of CSV result data"
        )
    cmd.add_argument \
        ( '-d', '--variant'
        , help    = "Variant of DE, one of rand/best default=%(default)s"
        , default = 'best'
        )
    cmd.add_argument \
        ( '-c', '--cross'
        , help    = "Crossover type, one of bin/exp, default=%(default)s"
        , default = 'bin'
        )
    cmd.add_argument \
        ( '-C', '--crossover-rate'
        , help    = "Crossover rate default=%(default)s"
        , dest    = 'Cr'
        , type    = float
        , default = 1.0
        )
    cmd.add_argument \
        ( '-D', '--dither'
        , type    = float
        , help    = "Dither used, default=%(default)s"
        , default = 0.0
        )
    cmd.add_argument \
        ( '-F', '--scale-factor'
        , help    = "Base DE scale factor F, default=%(default)s"
        , default = 0.85
        , dest    = 'F'
        , type    = float
        )
    cmd.add_argument \
        ( '-i', '--dither-per-individual'
        , help    = "Uses dither per individual"
        , dest    = 'dither_p_i'
        , default = False
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '-J', '--jitter'
        , type    = float
        , help    = "Jitter used, default=%(default)s"
        , default = 0.001
        )
    cmd.add_argument \
        ( '-P', '--scale-with_popsize'
        , help    = "Scale F negatively with popsize, default=%(default)s"
        , default = 0.0005
        , dest    = 'F_dec'
        , type    = float
        )
    cmd.add_argument \
        ( '-p', '--popsize'
        , type    = int
        , help    = "Population size, default=%(default)s"
        , dest    = 'np'
        , default = None
        )
    cmd.add_argument \
        ( '-s', '--sort-population'
        , help    = "Sort population by angle/radius"
        , default = False
        , dest    = 'sort'
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '-u', '--use-prefilter'
        , help    = "Uses prefilter before optimized filter"
        , default = False
        , dest    = 'prefilter'
        , action  = 'store_true'
        )
    args = cmd.parse_args ()
    ed = Eval_Data (args)
    ed.plot_eval_success ()
# end def main

if __name__ == '__main__':
    main ()
