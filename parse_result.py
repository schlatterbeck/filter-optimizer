#!/usr/bin/python3

import sys
import os
from csv import DictWriter

fields = ('variant', 'cross', 'np', 'F', 'sort', 'idx', 'eval', 'neval', 'iter')
dw = DictWriter (sys.stdout, delimiter = ';', fieldnames = fields)
dw.writerow (dict ((f, f) for f in fields))

#['fiopt/fiopt', 'best', 'bin', '400', 'F0.85', 'nosort', '9']

for fn in sys.argv [1:] :
    n, e = os.path.splitext (fn)
    params = n.split ('-')
    variant = params [1]
    cross   = params [2]
    np      = int (params [3])
    F       = float (params [4].lstrip ('F'))
    srt     = params [5] == 'sort'
    idx     = int (params [6])
    if not srt :
        assert params [5] == 'nosort'
    with open (fn, 'r') as f :
        found = False
        for line in f :
            if line.startswith ('The Best Evaluation:') :
                found = True
                eval  = float (line.split (':', 1) [1].strip ().rstrip ('.'))
            if found and line.startswith ('Iter:') :
                t, v1, t2, v2 = line.split ()
                iter   = int (v1)
                neval  = int (v2)
        d = dict \
            ( variant = variant
            , cross   = cross
            , np      = str (np)
            , F       = '%2.10f' % F
            , sort    = str (int (srt))
            , idx     = str (idx)
            , eval    = '%g' % eval
            , neval   = str (neval)
            , iter    = str (iter)
            )
        dw.writerow (d)
