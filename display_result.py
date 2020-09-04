#!/usr/bin/python3

import sys
from csv  import DictReader
from math import sqrt
import matplotlib.pyplot as plt
import numpy as np

def extract_data (key) :
    assert key [0] == 'best'
    assert key [1] == 'bin'
    assert key [4] == '0'
    assert float (key [3]) == 0.85
    return int (key [2])
# end def extract_data

def plot_neval (rbk) :
    fig  = plt.figure ()
    ax1  = fig.add_subplot (111)
    x    = []
    y1   = []
    y2   = []
    yerr = []
    nev  = []
    xmin = 1e6
    xmax = -1
    for k in rbk :
        r = rbk [k]
        if 'mean' not in r :
            continue
        n = extract_data (k)
        x.append (n)
        if n < xmin :
            xmin = n
        if n > xmax :
            xmax = n
        y1.append (r ['mean'])
        y2.append ((r ['success']) / (r ['success'] + r ['fail']) * 100)
        nev.append (r ['neval'])
    #ax1.plot (x, y)
    bp = ax1.boxplot (nev, positions = x, widths = 10)
    plt.title  ('Evaluations, Successes')
    plt.ylabel ('Evals', color = bp ['medians'][0].get_color ())
    plt.xlabel ('NP')
    ax1.set_xlim (xmin - 10, xmax + 10, auto = True)
    ax2 = ax1.twinx ()
    p, = ax2.plot   (x, y2)
    plt.ylabel ('Successes (%)', color = p.get_color ())
    plt.show ()
# end def plot_neval

def plot_nsuccess (rbk) :
    x = []
    y = []
    for k in rbk :
        r = rbk [k]
        if not r ['success'] :
            continue
        n = extract_data (k)
        x.append (n)
        y.append ((r ['success']) / (r ['success'] + r ['fail']) * 100)
    fig = plt.figure ()
    ax1 = fig.add_subplot (111)
    ax1.plot   (x, y)
    plt.title  ('Number of successes')
    plt.ylabel ('Successes (%)')
    plt.xlabel ('NP')
    plt.show ()
# end def plot_nsuccess

result_by_key = {}
with open (sys.argv [1], 'r')  as f :
    dr = DictReader (f, delimiter = ';')
    key_attributes = dr.fieldnames [:5]
    for rec in dr : 
        key = tuple (rec [k] for k in key_attributes)
        if key not in result_by_key :
            result_by_key [key] = dict \
                ( success = 0
                , fail    = 0
                , eval    = []
                , neval   = []
                )
        if float (rec ['eval']) == 0 :
            result_by_key [key]['success'] += 1
            result_by_key [key]['neval'].append (int (rec ['neval']))
        else :
            result_by_key [key]['fail'] += 1
            result_by_key [key]['eval'].append (float (rec ['eval']))
for k in result_by_key :
    r = result_by_key [k]
    r ['eval']  = np.array (r ['eval'])
    r ['neval'] = np.array (r ['neval'])
    n = r ['success']
    if n :
        r ['mean'] = sum (r ['neval']) / n
        r ['stdd']  = sqrt (sum ((r ['neval'] - r ['mean']) ** 2)) / n
#plot_nsuccess (result_by_key)
plot_neval    (result_by_key)
