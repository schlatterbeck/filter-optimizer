#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
from scipy  import signal
from bisect import bisect_left
from copy   import copy
from rsclib.iter_recipes import pairwise

def update_conjugate_complex (numbers):
    """ Modify numbers in-place to add conjugate complex numbers"""
    n2 = [k.conjugate () for k in numbers if k.imag]
    numbers.extend (n2)
# end def update_conjugate_complex

class Filter_Bound (object):

    def __init__ \
        ( self, xmin, xmax, ymin, ymax
        , n = 6, use_cos = False, xx = []
        , scale_by_pi = True
        ):
        self.xmin        = xmin
        self.xmax        = xmax
        self.ymin        = ymin
        self.ymax        = ymax
        self.scale_by_pi = scale_by_pi
        self.vals = [xmin, xmax, ymin, ymax]
        a = np.array (range (n)) / (n - 1.0)
        if use_cos:
            a = np.cos (a * np.pi) / -2.0 + 0.5
        self.x = a * (xmax - xmin) + xmin
        if scale_by_pi:
            self.x *= 2 * np.pi
        self.y = a * (ymax - ymin) + ymin
        if xx:
            self.append (*xx)
    # end def __init__

    @classmethod
    def Parse (cls, s, scale_by_pi = True):
        args = s.split (',')
        l = len (args)
        if not 4 <= l <= 6:
            raise ValueError ("Invalid number of parameters: %d" % l)
        xmin, xmax, ymin, ymax = (float (x) for x in args [:4])
        n = 31
        if l > 4:
            n = int (args [4])
        use_cos = False
        if l > 5:
            use_cos = bool (int (args [5]))
        return cls \
            (xmin, xmax, ymin, ymax, n, use_cos, scale_by_pi = scale_by_pi)
    # end def Parse

    def __str__ (self):
        return ','.join (str (x) for x in self.vals)
    # end def __str__
    __repr__ = __str__

    def append (self, *xx):
        self.x = np.append (self.x, np.array (xx) * 2 * np.pi)
        self.y = np.append (self.y, [self.interpolate (k) for k in xx])
    # end def append

    def copy (self):
        cp = self.__class__ (self.xmin, self.xmax, self.ymin, self.ymax)
        cp.x = copy (self.x)
        cp.y = copy (self.y)
        cp.scale_by_pi = self.scale_by_pi
        return cp
    # end def copy

    def interpolate (self, x):
        assert self.xmin <= x <= self.xmax
        d = (x - self.xmin) / (self.xmax - self.xmin)
        return (d * (self.ymax - self.ymin) + self.ymin)
    # end def interpolate

    def plot (self, ax, scatter = False):
        if scatter:
            raise NotImplementedError ('Scatter plot not yet implemented')
        else:
            X = np.array ([self.xmin, self.xmax])
            Y = np.array ([self.ymin, self.ymax])
            if not self.scale_by_pi:
                X /= 2 * np.pi
            ax.plot (X, Y, 'g')
    # end def plot

# end class Filter_Bound

class Filter_Bounds (object):

    def __init__ (self, * bounds, is_lower = False):
        self.bounds = list (sorted (bounds, key = lambda b: b.xmin))
        self.lower  = [x.xmin for x in self.bounds]
        self.is_lower = is_lower
        self.by_x = {}
        for b in bounds:
            for x, y in zip (b.x, b.y):
                if x in self.by_x:
                    if self.is_lower:
                        if y > self.by_x [x]:
                            self.by_x [x] = y
                    else:
                        if y < self.by_x [x]:
                            self.by_x [x] = y
                else:
                    self.by_x [x] = y
        self.x = np.array (sorted (self.by_x))
        self.y = np.array ([self.by_x [i] for i in self.x])
    # end def __init__

    @classmethod
    def Parse (cls, s, is_lower = False, delimiter = ', ', **kw):
        s = s.strip ()
        s = s.lstrip ('[')
        s = s.rstrip (']')
        bounds = []
        if not s:
            return cls (is_lower = is_lower)
        for fb in s.split (delimiter):
            bounds.append (Filter_Bound.Parse (fb, **kw))
        return cls (*bounds, is_lower = is_lower)
    # end def Parse

    def __bool__ (self):
        return len (self.x) > 0
    # end def __bool__

    def __iter__ (self):
        for x, y in zip (self.x, self.y):
            yield (x, y)
    # end def __iter__

    def __str__ (self):
        r = [str (b) for b in self.bounds]
        return '[' + '; '.join (r) + ']'
    # end def __str__
    __repr__ = __str__

    def copy (self):
        bounds = []
        for b in self.bounds:
            bounds.append (b.copy ())
        return self.__class__ (*bounds, is_lower = self.is_lower)
    # end def copy

    def interpolate (self, x):
        idx = bisect_left (self.lower, x)
        if idx == 0 and self.bounds [idx].xmin > x:
            raise ValueError ("Too small: %s" % x)
        if idx >= len (self.lower):
            idx = idx - 1
        if idx == len (self.lower) - 1 and self.bounds [idx].xmax < x:
            raise ValueError ("Too large: %s" % x)
        return self.bounds [idx].interpolate (x)
    # end def interpolate

    def plot (self, ax, scatter = False):
        for b in self.bounds:
            b.plot (ax, scatter)
    # end def plot

    def y_transform (self, offset = 0, multiplier = 1):
        return self.y * multiplier + offset
    # end def y_transform

# end class Filter_Bounds

# Defaults from the original paper and defaults when nothing is specified
default_upper_magnitude = Filter_Bounds \
    ( Filter_Bound \
	( 0.0,     0.04938, 0.01,  0.025
	, xx = (0.01,   0.02,  0.03, 0.04)
	)
    , Filter_Bound \
	( 0.04938, 0.2716,  0.025, 0.025, 73
	, xx = ( 0.05
	       , 0.07,   0.076,   0.0765, 0.077
	       , 0.0786, 0.07865, 0.0787, 0.079
	       , 0.08,   0.0808,  0.0809
	       , 0.10,   0.11,    0.12,   0.13,   0.15, 0.17, 0.18, 0.19
	       , 0.1995, 0.2,     0.205,  0.21,   0.215
	       , 0.2162, 0.2163,  0.2164, 0.217,  0.218
	       , 0.22,   0.222
	       , 0.223,  0.224,   0.225,  0.226,  0.227, 0.228
	       , 0.23,   0.26,    0.2625, 0.2675
	       )
	)
    , Filter_Bound \
	( 0.2716,  0.3334,  0.05,  0.05,  43
	, xx = ( 0.278,  0.279,   0.2795,  0.28,   0.2805, 0.281
	       , 0.284,  0.28441, 0.2845,  0.285,  0.286,  0.2865
	       , 0.294,  0.295,   0.2955
	       , 0.296,  0.2965,  0.297,   0.298,  0.3
	       , 0.306,  0.315,   0.316,   0.317,  0.318,  0.3194
	       , 0.32,   0.3205,  0.3206,  0.321
	       , 0.3211, 0.3212,  0.3213,  0.3214, 0.3215, 0.3218
	       , 0.322,  0.3225,  0.32275, 0.3228
	       , 0.323,  0.3232,  0.3234,  0.3236, 0.3238
	       , 0.324,  0.3242,  0.3243,  0.3244
	       , 0.325 , 0.3254,  0.3258
	       , 0.3262, 0.32625
	       , 0.3265, 0.327,   0.3272, 0.3273, 0.3274
	       )
	)
    , Filter_Bound \
	( 0.3334,  0.395, -12,   -12,     43
	, xx = ( 0.33341, 0.33342, 0.33343, 0.33344
	       , 0.34,    0.3405
	       , 0.342,   0.3425,  0.3426, 0.3427, 0.3428
	       , 0.343,   0.34325, 0.3434
	       , 0.344,   0.3443,  0.3446, 0.3447
	       , 0.345,   0.3454
	       )
	)
    , Filter_Bound \
	( 0.395,   0.5,   -40,   -40,     37
	, xx = ( 0.39501, 0.39502, 0.39503
	       , 0.4048,  0.405
	       , 0.422,   0.4222,  0.4225
	       , 0.423,   0.42325, 0.4236, 0.4237, 0.4238
	       , 0.424,   0.4246,  0.4247, 0.4248
	       , 0.425,   0.426
	       , 0.4272,  0.4273
	       , 0.498,   0.499
	       )
	)
    )

default_lower_magnitude = Filter_Bounds \
    ( Filter_Bound (0.0,     0.04938, -0.01,  -0.025)
    , Filter_Bound \
	( 0.04938, 0.2716,  -0.025, -0.025, 43
	, xx = ( 0.11,  0.12,   0.13,  0.14,  0.141
	       , 0.146, 0.147,  0.148
	       , 0.15,  0.1525, 0.153, 0.152
	       , 0.155, 0.157
	       , 0.158, 0.15832, 0.15833, 0.15834
	       , 0.15905
	       , 0.162, 0.163
	       , 0.245, 0.246,  0.247, 0.248, 0.249
	       , 0.25,  0.255
	       , 0.26,  0.265,  0.268, 0.269
	       , 0.27,  0.2705
	       , 0.271597, 0.271598, 0.271599
	       )
	)
    , Filter_Bound \
	( 0.2716,  0.284,   -0.05,  -0.05
	, xx = ( 0.275, 0.276, 0.277, 0.278, 0.279
	       , 0.28,  0.281, 0.282, 0.283, 0.2835
	       )
	)
    , is_lower = True
    )

default_upper_delay = Filter_Bounds \
    ( Filter_Bound \
	( 0.0, 0.284,  0.10125,  0.30375, 17
	, xx = (0.2834, 0.2835, 0.2836, 0.2837, 0.2338, 0.2839)
	)
    )

default_lower_delay = Filter_Bounds \
    ( Filter_Bound \
	( 0.0, 0.284, -0.10125, -0.30375, 17
	, xx = (0.2834, 0.2835, 0.2836, 0.2837, 0.2338, 0.2839)
	)
    , is_lower = True
    )

def plot_response \
    ( w, h
    , title = '', do_angle = False
    , fs    = None
    , logx  = False, logy = True
    , xmin  = None,  xmax = None
    , ymin  = None,  ymax = None
    , bounds = []
    ):
    fig = plt.figure ()
    ax  = fig.add_subplot (111)
    if logx:
        ax.set_xscale ('log')
    t = 'Frequency response'
    if title:
        if title.startswith ('-'):
            t = title [1:]
        else:
            t = t + ' ' + title
    plt.title (t)
    xlabel = 'Freq [rad/sample]'
    if fs is not None:
        w = np.array (w) * fs / (2 * np.pi)
        xlabel = 'Freq (Hz)'
        if fs == 1.0:
            xlabel = '$\\Omega$'
    for b in bounds:
        b.plot (ax)
    if logy:
        ax.plot (w, 20 * np.log10 (abs (h)), 'b')
        plt.ylabel ('Amplitude (dB)', color = 'b')
    else:
        ax.plot (w, abs (h), 'b')
        plt.ylabel ('Amplitude (lin.)', color = 'b')
    plt.xlabel (xlabel)
    plt.grid (which = 'both')

    if do_angle:
        ax2 = ax.twinx ()
        angles = np.unwrap (np.angle (h))
        ax2.plot (w, angles, 'g')
        plt.ylabel ('Angle (rad)', color = 'g')
    plt.axis ('tight')
    ax.set_xlim (xmin, xmax, auto = True)
    if ymin is not None or ymax is not None:
        ax.set_ylim (ymin, ymax, auto = True)
    plt.show ()
# end def plot_response

def plot_delay \
    ( w, d, title = "", fs = None
    , logx = False, xmin = 0.0, xmax = None, ymin = None, ymax = None
    , bounds = [], auto_ylimit = True
    ):

    fig = plt.figure ()
    ax  = fig.add_subplot (111)
    if logx:
        ax.set_xscale ('log')
    t = 'Group delay'
    if title:
        if title.startswith ('-'):
            t = title [1:]
        else:
            t = t + ' ' + title
    plt.title (t)
    xlabel = 'Freq [rad/sample]'
    if fs is not None:
        w = np.array (w) * fs / (2 * np.pi)
        xlabel = 'Freq (Hz)'
        if fs == 1.0:
            xlabel = '$\\Omega$'

    # Move curve to upper bound
    bounds  = [b for b in bounds if b]
    ubounds = [b for b in bounds if not b.is_lower]
    lbounds = [b for b in bounds if b.is_lower]
    if bounds:
        delta = None
        for x, y in zip (w, d):
            for b in ubounds:
                try:
                    yb = b.interpolate (x)
                except ValueError:
                    continue
                dd = y - yb
                if delta is None or dd > delta:
                    delta = dd
        for b in bounds:
            ax.plot (b.x * fs / (2 * np.pi), b.y_transform (delta), 'g')
        if auto_ylimit and not ymin and not ymax:
            miny = min (min (b.y_transform (delta) for b in lbounds))
            maxy = max (max (b.y_transform (delta) for b in ubounds))
            dif  = (maxy - miny) * 2
            miny -= dif / 2
            maxy += dif / 2
            ymin = miny
            ymax = maxy

    plt.plot (w, d, 'b')
    plt.ylabel ('Delay (samples)', color = 'b')
    plt.xlabel (xlabel)

    plt.grid ()
    plt.axis ('tight')
    ax.set_xlim (xmin, xmax, auto = True)
    if ymin is not None or ymax is not None:
        ax.set_ylim (ymin, ymax, auto = True)
    plt.show ()
# end def plot_delay

def pole_zero_plot \
    (poles, zeros, limit = 1e6, title = '', show_uc = True, ax = None):
    fig = plt.figure ()
    ax  = fig.add_subplot (111)
    poles = np.array (poles)
    zeros = np.array (zeros)
    m1 = m2 = 1
    if len (poles):
        m1 = max (abs (poles))
    if len (zeros):
        m2 = max (abs (zeros))
    m  = max (m1, m2) + 1
    if m > limit:
        m = limit
    ax.plot (np.real (zeros), np.imag (zeros), 'ob')
    ax.plot (np.real (poles), np.imag (poles), 'xr')
    if show_uc:
        c1 = plt.Circle \
            ((0, 0), 1, color = 'black', fill = False, linewidth = 0.25)
        ax.add_artist (c1)
    plt.legend (['Zeros', 'Poles'], loc=2)
    t = 'Pole / Zero Plot'
    if title:
        t = t + ' ' + title
    plt.title  (t)
    plt.ylabel ('Real')
    plt.xlabel ('Imag')
    plt.grid()
    plt.xlim (-m, m)
    plt.ylim (-m, m)
    #plt.gca ().set_aspect ('equal', adjustable='box')
    ax.set_aspect ('equal', adjustable='box')
    plt.show()
# end def pole_zero_plot
