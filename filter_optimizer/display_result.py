#!/usr/bin/python3

import os
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
        self.result_by_key = {}
        self.x_idx  = None
        self.x_axis = None
        self.keys   = []
        for fn in args.filename:
            with open (fn, 'r')  as f:
                self.parse_file (fn, f)
        if not self.result_by_key:
            print ("No keys specified found")
            sys.exit (23)
    # end def __init__

    def parse_file (self, fn, f):
        dr = DictReader (f, delimiter = ';')
        if 'randseed' in dr.fieldnames:
            key_attributes = dr.fieldnames [:-4]
        else:
            key_attributes = dr.fieldnames [:5]
            if dr.fieldnames [5] == 'Cr':
                key_attributes = dr.fieldnames [:6]
        if self.args.by_filename:
            key_attributes.append ('experiment')
        for i, name in enumerate (key_attributes):
            arg = getattr (self.args, name, None)
            if  (  arg is None
                or arg == ''
                or isinstance (arg, Number) and arg < 0
                ):
                if self.x_axis is None or self.x_axis == name:
                    self.x_axis = name
                    self.x_idx  = i
                    self.x_name = name
                else:
                    raise ValueError \
                        ('(More than) two key attributes used for X: %s, %s'
                        % (name, self.x_name)
                        )
            else:
                if name not in self.keys:
                    self.keys.append (name)
        if 'Cr' not in self.keys and self.x_name != 'Cr':
            self.keys.append ('Cr')
        if 'prefilter' not in self.keys and self.x_name != 'prefilter':
            self.keys.append ('prefilter')
        if 'jitter' not in self.keys and self.x_name != 'jitter':
            self.keys.append ('jitter')
        if 'dither' not in self.keys and self.x_name != 'dither':
            self.keys.append ('dither')
        if self.args.verbose:
            print \
                ( "Trying to match: %s"
                % (', '.join ('%s: %s' % (k, getattr (self.args, k))
                   for k in self.keys)
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
            if 'experiment' not in rec:
                rec ['experiment'] = os.path.splitext \
                    (os.path.basename (fn)) [0]

            do_continue = False
            for k in self.keys:
                arg = getattr (self.args, k)
                if arg and arg != rec [k]:
                    do_continue = True
                    break
            if do_continue:
                continue
            key = tuple (rec [k] for k in key_attributes)
            if key not in self.result_by_key:
                self.result_by_key [key] = dict \
                    ( success = 0
                    , fail    = 0
                    , eval    = []
                    , neval   = []
                    )
            if rec ['eval'] == 0:
                self.result_by_key [key]['success'] += 1
                self.result_by_key [key]['neval'].append (rec ['neval'])
            else:
                self.result_by_key [key]['fail'] += 1
                if self.args.count_unsuccessful:
                    self.result_by_key [key]['neval'].append (rec ['neval'])
                self.result_by_key [key]['eval'].append (rec ['eval'])
        for k in self.result_by_key:
            r = self.result_by_key [k]
            r ['eval']  = np.array (r ['eval'])
            r ['neval'] = np.array (r ['neval'])
            n = len (r ['neval'])
            if n:
                r ['mean'] = sum (r ['neval']) / n
                r ['stdd'] = sqrt (sum ((r ['neval'] - r ['mean']) ** 2)) / n
    # end def parse_file

    def plot_eval_success (self):
        if self.x_idx is None:
            exit ('No index to compare')
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
            if isinstance (a, Number):
                if a < xmin:
                    xmin = a
                if a > xmax:
                    xmax = a
            y2.append ((r ['success']) / (r ['success'] + r ['fail']) * 100)
            if r ['success'] or self.args.count_unsuccessful:
                y1.append (r ['mean'])
                nev.append (r ['neval'])
            else:
                y1.append (0)
                nev.append (np.array ([]))

        plt.title \
            ( 'Evaluations, Successes\n'
            + ' '.join
                ( '='.join ((k, str (getattr (self.args, k))))
                  for k in self.keys if k in legend
                )
            )
        plt.xlabel (self.x_name)
        tick = (xmax - xmin) / len (x) / 2.
        ml   = max (len (r) for r in nev)
        pos  = x
        if not isinstance (x [0], Number):
            pos  = np.arange (0, 1, 1 / len (x))
            tick = 1 / len (x)
        if ml:
            if len (x) == 1:
                bp = ax1.boxplot (nev [0] / 1000, positions = pos)
            else:
                nev1000 = [n / 1000 for n in nev]
                bp = ax1.boxplot (nev1000, positions = pos, widths = tick)
            plt.ylabel \
                ('Evals (thousands)', color = bp ['medians'][0].get_color ())
        ax1.set_xlim (xmin - tick / 3 * 2, xmax + tick / 3 * 2, auto = False)
        ax2 = ax1.twinx ()
        if not isinstance (x [0], Number):
            ax2.set_xticklabels (x, fontsize = 8)
        if len (x) == 1:
            p, = ax2.plot   (pos, y2, 'o', markersize = 5)
        else:
            p, = ax2.plot   (pos, y2, 'o-', markersize = 5)
        plt.ylabel ('Successes (%)', color = p.get_color ())
        plt.show ()
    # end def plot_eval_success

# end class Eval_Data

def main ():
    cmd = ArgumentParser ()
    cmd.add_argument \
        ( 'filename'
        , help    = "File name of CSV result data"
        , nargs   = '+'
        )
    cmd.add_argument \
        ( '-d', '--variant'
        , help    = "Variant of DE, one of rand/best default=%(default)s"
        , default = 'best'
        )
    cmd.add_argument \
        ( '--by-filename'
        , help    = "Compare by filename during eval"
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '--count-unsuccessful'
        , help    = "Count unsuccessful tries"
        , action  = 'store_true'
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
        , default = 0.1
        )
    cmd.add_argument \
        ( '-F', '--scale-factor'
        , help    = "Base DE scale factor F, default=%(default)s"
        , default = 0.87
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
        , default = 150
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
    cmd.add_argument \
        ( '-V', '--verbose'
        , help    = "More verbose reporting what we do"
        , action  = 'store_true'
        )
    args = cmd.parse_args ()
    ed = Eval_Data (args)
    ed.plot_eval_success ()
# end def main

if __name__ == '__main__':
    main ()
