#!/usr/bin/env python3
# Copyright (C) 2020-23 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ****************************************************************************

import sys
from setuptools import setup
sys.path.insert (1, '.')
from filter_optimizer import __version__

with open ('README.rst') as f:
    description = f.read ()

license     = 'MIT License'
rq          = '>=3.7'
setup \
    ( name             = "filter-optimizer"
    , version          = __version__
    , description      =
        "Optimize digital filters with differential evolution"
    , long_description = ''.join (description)
    , long_description_content_type='text/x-rst'
    , license          = license
    , author           = "Ralf Schlatterbeck"
    , author_email     = "rsc@runtux.com"
    , install_requires = ['matplotlib', 'numpy', 'scipy', 'rsclib']
    , packages         = ['filter_optimizer']
    , platforms        = 'Any'
    , url              = "https://github.com/schlatterbeck/filter-optimizer"
    , python_requires  = rq
    , entry_points     = dict
        ( console_scripts =
            [ 'filter-optimizer=filter_optimizer.filter_optimizer:main'
            , 'filter-display-result=filter_optimizer.display_result:main'
            , 'filter-show-from-log=filter_optimizer.showfromlog:main'
            , 'filter-parse-result=filter_optimizer.parse_result:main'
            ]
        )
    , classifiers      = \
        [ 'Development Status :: 3 - Alpha'
        , 'License :: OSI Approved :: ' + license
        , 'Operating System :: OS Independent'
        , 'Programming Language :: Python'
        , 'Intended Audience :: Science/Research'
        , 'Intended Audience :: Other Audience'
        ]
    )
