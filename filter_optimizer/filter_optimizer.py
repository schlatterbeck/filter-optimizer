#!/usr/bin/python3

from argparse   import ArgumentParser
from scipy      import signal
from bisect     import bisect
import pga
import sys
import numpy as np
from rsclib.autosuper import autosuper
from . import filterplot

class Filter_Opt (pga.PGA, autosuper):
    """ Optimize a filter with differential evolution
        A note on params: FIWIZ seems to use
        - A base F of 0.5
        - Dither of 0.5
        - A jitter of 0.001 added
        - Subtract NP * 0.0005
        This would translate to our centered dither/jitter:
        - base F of 0.5 + 0.25 + 0.0005 = 0.7505
        - Dither 0.5
        - Jitter 0.001
        - Subtract NP * 0.0005
    """

    def __init__ (self, args):
        self.last_best  = 1-6
        self.stag_count = 0
        self.args       = args
        self.npoles     = args.poles
        self.nzeros     = args.zeros
        self.do_stop    = False
        # parameters in the form radius, angle
        # first the zeros then the poles
        # All angles in the range   [0, 0.5]
        # zeros radius in the range [0, 5]
        # poles radius in the range [0, 0.999]
        ini = []
        for k in range (self.nzeros):
            ini.append ((0, 5))
            ini.append ((0, 0.5))
        for k in range (self.npoles):
            ini.append ((0, 0.999))
            ini.append ((0, 0.5))
        de_cross_type = pga.PGA_DE_CROSSOVER_BIN
        if self.args.exponential_crossover:
            de_cross_type = pga.PGA_DE_CROSSOVER_EXP
        v = self.args.de_variant
        if v == 'eo':
            v = 'either_or'
        variant = getattr (pga, 'PGA_DE_VARIANT_' + v.upper ())
        f = ( self.args.scale_factor
            - (self.args.popsize * self.args.scale_with_popsize)
            )
        d = dict \
            ( maximize                    = False
            , pop_size                    = self.args.popsize
            , num_replace                 = self.args.popsize
            , print_options               = [pga.PGA_REPORT_STRING]
            #, print_frequency             = 200
            , init                        = ini
            , select_type                 = pga.PGA_SELECT_LINEAR
            , pop_replace_type            = pga.PGA_POPREPL_PAIRWISE_BEST
            #, pop_replace_type            = pga.PGA_POPREPL_RTR
            #, rtr_window_size             = 2
            , mutation_bounce_back        = True
            , mutation_only               = True
            , mutation_type               = pga.PGA_MUTATION_DE
            , DE_variant                  = variant
            , DE_crossover_prob           = self.args.crossover_rate
            , DE_jitter                   = self.args.jitter
            , DE_dither                   = self.args.dither
            , DE_dither_per_individual    = self.args.dither_per_individual
            , DE_scale_factor             = f
            , DE_crossover_type           = de_cross_type
            , random_seed                 = self.args.random_seed
            )
        stop = []
        if self.args.max_no_change:
            d ['max_no_change'] = self.args.max_no_change
            stop.append (pga.PGA_STOP_NOCHANGE)
        if self.args.max_generations != 0:
            stop.append (pga.PGA_STOP_MAXITER)
            d ['max_GA_iter'] = self.args.max_generations
        # Default to max_evals if no max_generations given
        if not self.args.max_evals and not self.args.max_generations:
            stop.append (pga.PGA_STOP_MAXITER)
            d ['max_GA_iter'] = self.args.max_generations
        if stop:
            d ['stopping_rule_types'] = stop
        if args.max_evals and not args.max_generations:
            d ['max_GA_iter'] = 0x7FFFFFFF
        super ().__init__ (float, 2 * (self.npoles + self.nzeros), **d)
        self.udb = filterplot.Filter_Bounds \
            (*self.args.magnitude_upper_bound)
        self.ldb = filterplot.Filter_Bounds \
            (*self.args.magnitude_lower_bound, is_lower = True)
        self.udelay = filterplot.Filter_Bounds \
            (*self.args.delay_upper_bound)
        self.ldelay = filterplot.Filter_Bounds \
            (*self.args.delay_lower_bound, is_lower = True)
        if not (self.udb or self.ldb or self.udelay or self.ldelay):
            self.default_constraints ()
        self.dbx = list (sorted (set (np.concatenate
            ((self.ldb.x, self.udb.x)))))
        self.delay_x = list (sorted (set (np.concatenate
            ((self.udelay.x, self.ldelay.x)))))
        # Pre-Filter, only makes sense for original example
        self.fir  = \
            [ -0.033271, -0.019816,  0.169865,  0.415454
            ,  0.415454,  0.169865, -0.019816, -0.033271
            ]
        fir_w, self.fir_h = signal.freqz (self.fir, [1.0], self.dbx)
        self.a0 = self.args.gain
    # end def __init__

    def default_constraints (self):
        self.udb = filterplot.default_upper_magnitude
        self.ldb = filterplot.default_lower_magnitude
        self.udelay = filterplot.default_upper_delay
        self.ldelay = filterplot.default_lower_delay
    # end def default_constraints

    def phenotype (self, p, pop):
        def ga (i):
            return self.get_allele (p, pop, i)
        # pole offset in gene
        po = 2 * self.nzeros
        zeros = [ga (2*k)    * np.e ** (2j * np.pi * ga (2*k+1))
                 for k in range (self.nzeros)]
        poles = [ga (2*k+po) * np.e ** (2j * np.pi * ga (2*k+po+1))
                 for k in range (self.npoles)]
        self.update_conjugate_complex (zeros)
        self.update_conjugate_complex (poles)
        (b, a)  = signal.zpk2tf (zeros, poles, self.a0)
        return (zeros, poles, b, a)
    # end def phenotype

    def evaluate (self, p, pop):
        zeros, poles, b, a = self.phenotype (p, pop)
        wgd, gd = signal.group_delay ((b, a), self.delay_x)
        w, h    = signal.freqz       (b, a, self.dbx)
        if self.args.use_prefilter:
            hf  = self.fir_h * h
        else:
            hf  = h
        db      = 20 * np.log10 (abs (hf))
        dbdict  = dict ((x, y) for x, y in zip (self.dbx, db))
        dldict  = dict ((x, y) for x, y in zip (self.delay_x, gd))

        evf = 0.0
        ev  = 0.0
        for xb, yb in self.udb:
            if dbdict [xb] > yb:
                ev += (dbdict [xb] - yb) ** 2
            elif self.args.optimize_further and not ev:
                evf += min (abs (dbdict [xb] - yb) ** 0.5, 1.0)
        for xb, yb in self.ldb:
            if dbdict [xb] < yb:
                ev += (dbdict [xb] - yb) ** 2
            elif self.args.optimize_further and not ev:
                evf += min (abs (dbdict [xb] - yb) ** 0.5, 1.0)
        delaydelta = None
        # Shift the curve so that it touches the upper delay delta
        for xb, yb in self.udelay:
            delta = dldict [xb] - (yb / 2 * np.pi)
            if delaydelta is None or delta > delaydelta:
                delaydelta = delta
        # Check where the curve underflows the lower delay delta
        for xb, yb in self.ldelay:
            d = yb / (2 * np.pi)
            if dldict [xb] - delaydelta < d:
                ev += (dldict [xb] - delaydelta - d) ** 2
            elif self.args.optimize_further and not ev:
                evf += abs (dldict [xb] - delaydelta - d) ** 0.5
        if self.args.optimize_further and not ev:
            return -evf
        return ev
    # end def evaluate

    def stop_cond (self):
        best_idx = self.get_best_index (pga.PGA_OLDPOP)
        best_ev  = self.get_evaluation (best_idx, pga.PGA_OLDPOP)
        if not self.args.optimize_further and best_ev == 0:
            self.do_stop = True
            return True
        if self.args.max_evals and self.eval_count >= self.args.max_evals:
            self.do_stop = True
            return True
        # Experimental early stopping when stagnating
        if self.last_best - best_ev < self.last_best / 500:
            self.stag_count += 1
            if self.stag_count >= 200:
                self.do_stop = True
                return True
        else:
            self.stag_count = 0
        self.last_best = best_ev
        if self.check_stopping_conditions ():
            self.do_stop = True
        return self.do_stop
    # end def stop_cond

    def update_conjugate_complex (self, nums):
        """ Modify nums in-place to add conjugate complex numbers """
        n2 = [k.conjugate () for k in nums if k.imag]
        nums.extend (n2)
    # end def update_conjugate_complex

    def pre_eval (self, pop):
        if not self.args.sort_population:
            return
        ga  = self.get_allele
        # Unpack gene into pairs (angle, radius)
        for p in range (self.pop_size):
            zeros = \
                [( ga (p, pop, 2*i + 1)
                 , ga (p, pop, 2*i)
                 )
                 for i in range (self.nzeros)
                ]
            poles = \
                [( ga (p, pop, 2*i + 2*self.nzeros + 1)
                 , ga (p, pop, 2*i + 2*self.nzeros)
                 )
                 for i in range (self.npoles)
                ]
            # Sort by angle/radius
            zeros = list (sorted (zeros))
            poles = list (sorted (poles))
            # re-pack into gene
            for i in range (self.nzeros):
                self.set_allele (p, pop, 2*i,   zeros [i][1])
                self.set_allele (p, pop, 2*i+1, zeros [i][0])
            for i in range (self.npoles):
                self.set_allele (p, pop, 2*i + 2*self.nzeros,   poles [i][1])
                self.set_allele (p, pop, 2*i + 2*self.nzeros+1, poles [i][0])
    # end def pre_eval

    def _print (self, f, p, pop, n, offset):
        for k in range (n):
            e = ', '
            if k == n - 1:
                e = '\n'
            a = self.get_allele (p, pop, 2*k+offset)
            print ("%1.8f" % a, file = f, end = e)
    # end def _print

    def print_args (self, file):
        l = 0
        for k in self.args.__dict__:
            if len (k) > l:
                l = len (k)
        for k in sorted (self.args.__dict__):
            v = self.args.__dict__ [k]
            print (('%%-%ds: %%s' % l) % (k, v), file = file)
    # end def print_args

    def print_string (self, f, p, pop):
        #zeros, poles, b, a = self.phenotype (p, pop)
        print \
            ( "Iter: %s Evals: %s Stag: %s"
            % (self.GA_iter, self.eval_count, self.stag_count)
            , file = f
            )
        if self.do_stop:
            self.print_args (f)
        #print ('params.append \\', file = f)
        #print (" ([ ", file = f, end = '')
        #self._print (f, p, pop, self.nzeros, 0)
        #print (" ,  ", file = f, end = '')
        #self._print (f, p, pop, self.nzeros, 1)
        #print (" ,  ", file = f, end = '')
        #self._print (f, p, pop, self.npoles, 2 * self.nzeros)
        #print (" ,  ", file = f, end = '')
        #self._print (f, p, pop, self.npoles, 2 * self.nzeros + 1)
        #print (" ])", file = f)
        f.flush ()
        self.__super.print_string (f, p, pop)
        f.flush ()
    # end def print_string

# end class Filter_Opt

def main ():
    constraint_text = \
        """ gets 4 mandatory parameters separated with comma: min-x,
            max-x, min-y, max-y and two optional parameters: The number of
            points (default 31) and if we should apply raised cosine
            transform (making the points tighter at the bounds). Can be
            specified multiple times
        """
    cmd = ArgumentParser ()
    cmd.add_argument \
        ( '--crossover-rate'
        , help    = "Rate of DE crossover, default=%(default)s"
        , type    = float
        , default = 1.0
        )
    cmd.add_argument \
        ( '--de-variant'
        , help    = "Variant of DE algorithm, "
                    "one of rand/best/eo default=%(default)s"
        , default = 'best'
        )
    cmd.add_argument \
        ( '-L', '--delay-lower-bound'
        , help    = "Lower bound for delay in samples, " + constraint_text
        , default = []
        , action  = 'append'
        )
    cmd.add_argument \
        ( '-U', '--delay-upper-bound'
        , help    = "Upper bound for delay in samples, " + constraint_text
        , default = []
        , action  = 'append'
        )
    cmd.add_argument \
        ( '-D', '--dither'
        , help    = "Dither value to use, default=%(default)s"
        , default = 0.1
        , type    = float
        )
    cmd.add_argument \
        ( '--dither-per-individual'
        , help    = "Use dither per individual not per generation"
        , default = False
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '--exponential-crossover'
        , help    = "Use exp crossover (instead of bin)"
        , default = False
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '-k', '--gain'
        , help    = "Gain to apply for filter default=%(default)s, "
                    "set to 0 to auto-generate"
        , default = 0.00390625
        , type    = float
        )
    cmd.add_argument \
        ( '-J', '--jitter'
        , help    = "Jitter value to use, default=%(default)s"
        , default = 0.001
        , type    = float
        )
    cmd.add_argument \
        ( '-l', '--magnitude-lower-bound'
        , help    = "Lower bound for magnitude in dB, " + constraint_text
        , default = []
        , action  = 'append'
        )
    cmd.add_argument \
        ( '-u', '--magnitude-upper-bound'
        , help    = "Upper bound for magnitude in dB, " + constraint_text
        , default = []
        , action  = 'append'
        )
    cmd.add_argument \
        ( '-m', '--max-evals'
        , help    = "Maximum number of evaluations default=%(default)s"
        , default = 500000
        , type    = int
        )
    cmd.add_argument \
        ( '--max-generations'
        , type    = int
        , help    = "Maximum number of generations, default=%(default)s"
        , default = 0
        )
    cmd.add_argument \
        ( '--max-no-change'
        , help    = "Maximum number of generations without change before "
                    "stopping default=%(default)s"
        , default = 0
        , type    = int
        )
    cmd.add_argument \
        ( '-o', '--optimize-further'
        , help    = "Normally we stop when constraints are met, "
                    "this tries to further optimize the filter"
        , action  = "store_true"
        )
    cmd.add_argument \
        ( '-p', '--popsize'
        , type    = int
        , help    = "Population size, default=%(default)s"
        , default = 150
        )
    cmd.add_argument \
        ( '-F', '--scale-factor'
        , help    = "Base DE scale factor F, default=%(default)s "
                    "(popsize-dependent part is subtracted)"
        , default = 0.87
        , type    = float
        )
    cmd.add_argument \
        ( '--scale-with-popsize'
        , help    = "Subtract this value * popsize from scale-factor F."
                    " Set to 0 for turning off, default=%(default)s"
        , default = 0.0005
        , type    = float
        )
    cmd.add_argument \
        ( '-P', '--poles'
        , type    = int
        , help    = "Number of poles, default=%(default)s"
        , default = 4
        )
    cmd.add_argument \
        ( '-R', '--random-seed'
        , type    = int
        , help    = "Random number seed, default=%(default)s"
        , default = 42
        )
    cmd.add_argument \
        ( '--dont-scale-by-pi'
        , help    = "Scale X-values for constraints with 2*pi,"
                    " Values are either 0 <= x <= 0.5 and scaling is"
                    " performed or 0 <= x <= pi if no scaling is performed"
        , dest    = 'scale_by_pi'
        , default = True
        , action  = 'store_false'
        )
    cmd.add_argument \
        ( '--sort-population'
        , help    = "Sort population by angle/radius"
        , default = False
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '--use-prefilter'
        , help    = "Use pre-filter in addition to optimized filter"
        , default = False
        , action  = 'store_true'
        )
    cmd.add_argument \
        ( '-Z', '--zeros'
        , type    = int
        , help    = "Number of zeros, default=%(default)s"
        , default = 5
        )
    args = cmd.parse_args ()
    for t in ('delay', 'magnitude'):
        for b in ('lower_bound', 'upper_bound'):
            n = '_'.join ((t, b))
            r = []
            for v in getattr (args, n):
                try:
                    parse = filterplot.Filter_Bound.Parse
                    r.append (parse (v, scale_by_pi = args.scale_by_pi))
                except ValueError as err:
                    print (cmd.usage)
                    exit ("Invalid value for %s: %s" % (n, v))
                setattr (args, n, r)
    pg = Filter_Opt (args)
    pg.run ()
# end def main

if __name__ == '__main__':
    main ()
