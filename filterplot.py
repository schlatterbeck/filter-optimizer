#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
from scipy  import signal
from bisect import bisect_left
from rsclib.iter_recipes import pairwise

def update_conjugate_complex (numbers) :
    """ Modify numbers in-place to add conjugate complex numbers"""
    n2 = [k.conjugate () for k in numbers if k.imag]
    numbers.extend (n2)
# end def update_conjugate_complex

class Filter_Bound (object) :

    def __init__ (self, xmin, xmax, ymin, ymax, n = 6, use_cos = False, xx = []) :
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        a = np.array (range (n)) / (n - 1.0)
        if use_cos :
            a = np.cos (a * np.pi) / -2.0 + 0.5
        self.x = (a * (xmax - xmin) + xmin) * 2 * np.pi
        self.y = a * (ymax - ymin) + ymin
        if xx :
            self.x = np.append (self.x, np.array (xx) * 2 * np.pi)
            self.y = np.append (self.y, [self.interpolate (k) for k in xx])

    # end def __init__

    def interpolate (self, x) :
        assert self.xmin <= x <= self.xmax
        d = (x - self.xmin) / (self.xmax - self.xmin)
        return (d * (self.ymax - self.ymin) + self.ymin)
    # end def interpolate

# end class Filter_Bound

class Filter_Bounds (object) :

    def __init__ (self, * bounds, is_lower = False) :
        self.bounds = list (sorted (bounds, key = lambda b: b.xmin))
        self.lower  = [x.xmin for x in self.bounds]
        self.is_lower = is_lower
        self.by_x = {}
        for b in bounds :
            for x, y in zip (b.x, b.y) :
                if x in self.by_x :
                    if self.is_lower :
                        if y > self.by_x [x] :
                            self.by_x [x] = y
                    else :
                        if y < self.by_x [x] :
                            self.by_x [x] = y
                else :
                    self.by_x [x] = y
        self.x = np.array (sorted (self.by_x))
        self.y = np.array ([self.by_x [i] for i in self.x])
    # end def __init__

    def add_offset (self, offset) :
        self.y = self.y + offset
    # end def add_offset

    def interpolate (self, x) :
        idx = bisect_left (self.lower, x)
        if idx == 0 and self.bounds [idx].xmin > x :
            raise ValueError ("Too small: %s" % x)
        if idx >= len (self.lower) :
            idx = idx - 1
        if idx == len (self.lower) - 1 and self.bounds [idx].xmax < x :
            raise ValueError ("Too large: %s" % x)
        return self.bounds [idx].interpolate (x)
    # end def interpolate

    def __iter__ (self) :
        for x, y in zip (self.x, self.y) :
            yield (x, y)
    # end def __iter__

# end class Filter_Bounds

def plot_response \
    ( w, h
    , title = '', do_angle = False
    , fs    = None
    , logx  = False, logy = True
    , xmin  = None,  xmax = None
    , ymin  = None,  ymax = None
    , constraints = []
    ) :
    fig = plt.figure ()
    ax1 = fig.add_subplot (111)
    if logx :
        ax1.set_xscale ('log')
    t = 'Frequency response'
    if title :
        if title.startswith ('-') :
            t = title [1:]
        else :
            t = t + ' ' + title
    plt.title (t)
    xlabel = 'Freq [rad/sample]'
    if fs is not None :
        w = np.array (w) * fs / (2 * np.pi)
        xlabel = 'Freq (Hz)'
        if fs == 1.0 :
            xlabel = '$\\Omega$'
    for x, y in constraints :
        ax1.plot (x, y, 'g')
    if logy :
        ax1.plot (w, 20 * np.log10 (abs (h)), 'b')
        plt.ylabel ('Amplitude (dB)', color = 'b')
    else :
        ax1.plot (w, abs (h), 'b')
        plt.ylabel ('Amplitude (lin.)', color = 'b')
    plt.xlabel (xlabel)
    plt.grid (which = 'both')

    if do_angle :
        ax2 = ax1.twinx ()
        angles = np.unwrap (np.angle (h))
        ax2.plot (w, angles, 'g')
        plt.ylabel ('Angle (rad)', color = 'g')
    plt.axis ('tight')
    ax1.set_xlim (xmin, xmax, auto = True)
    if ymin is not None or ymax is not None :
        ax1.set_ylim (ymin, ymax, auto = True)
    plt.show ()
# end def plot_response

def plot_delay \
    ( w, d, title = "", fs = None
    , logx = False, xmin = 0.0, xmax = None, ymin = None, ymax = None
    , constraints = [], auto_ylimit = True, d_in_samples = False
    ) :

    fig = plt.figure ()
    ax1 = fig.add_subplot (111)
    if logx :
        ax1.set_xscale ('log')
    t = 'Group delay'
    if title :
        if title.startswith ('-') :
            t = title [1:]
        else :
            t = t + ' ' + title
    plt.title (t)
    xlabel = 'Freq [rad/sample]'
    if fs is not None :
        w = np.array (w) * fs / (2 * np.pi)
        xlabel = 'Freq (Hz)'
        if fs == 1.0 :
            xlabel = '$\\Omega$'

    # FIXME: Needs further check
    #if not d_in_samples :
    #    d = d / (2 * np.pi)

    # If constraints given, asume the first are the upper
    # Move curve to upper bound
    bounds = []
    if constraints :
        for c in constraints :
            r = []
            for xy1, xy2 in pairwise (zip (c [0], c [1])) :
                if xy1 [0] == xy2 [0] :
                    continue
                r.append (Filter_Bound (xy1 [0], xy2 [0], xy1 [1], xy2 [1]))
            bounds.append (Filter_Bounds (* r))
        delta = None
        for x, y in zip (w, d) :
            try :
                yb = bounds [0].interpolate (x)
            except ValueError :
                break
            dd = y - yb
            if delta is None or dd > delta :
                delta = dd
        for b in bounds :
            b.add_offset (delta)
            ax1.plot (b.x * fs / (2 * np.pi), b.y, 'g')
        if auto_ylimit and not ymin and not ymax :
            miny = min (bounds [-1].y)
            maxy = max (bounds [0].y)
            dif  = (maxy - miny) * 2
            miny -= dif / 2
            maxy += dif / 2
            ymin = miny
            ymax = maxy

    plt.plot (w, d, 'b')
    plt.ylabel ('Delay', color = 'b')
    plt.xlabel (xlabel)

    plt.grid ()
    plt.axis ('tight')
    ax1.set_xlim (xmin, xmax, auto = True)
    if ymin is not None or ymax is not None :
        ax1.set_ylim (ymin, ymax, auto = True)
    plt.show ()
# end def plot_delay

def pole_zero_plot (poles, zeros, limit = 1e6, title = '', show_uc = True) :
    fig = plt.figure ()
    ax1 = fig.add_subplot (111)
    poles = np.array (poles)
    zeros = np.array (zeros)
    m1 = m2 = 1
    if len (poles) :
        m1 = max (abs (poles))
    if len (zeros) :
        m2 = max (abs (zeros))
    m  = max (m1, m2) + 1
    if m > limit :
        m = limit
    if show_uc :
        c1 = plt.Circle \
            ((0, 0), 1, color = 'black', fill = False, linewidth = 0.25)
        ax1.add_artist (c1)
    ax1.plot (np.real (zeros), np.imag (zeros), 'ob')
    ax1.plot (np.real (poles), np.imag (poles), 'xr')
    plt.legend (['Zeros', 'Poles'], loc=2)
    t = 'Pole / Zero Plot'
    if title :
        t = t + ' ' + title
    plt.title  (t)
    plt.ylabel ('Real')
    plt.xlabel ('Imag')
    plt.grid()
    plt.xlim (-m, m)
    plt.ylim (-m, m)
    #plt.gca ().set_aspect ('equal', adjustable='box')
    ax1.set_aspect ('equal', adjustable='box')
    plt.show()
# end def pole_zero_plot
