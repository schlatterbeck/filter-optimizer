#!/usr/bin/env python

from scipy import signal
import matplotlib.pyplot as plt
import numpy as np

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
