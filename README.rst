Optimization of Digital Filters
===============================

:Author: Ralf Schlatterbeck <rsc@runtux.com>

.. |--| unicode:: U+2013   .. en dash
.. |__| unicode:: U+2013   .. en dash without spaces
    :trim:
.. |_| unicode:: U+00A0 .. Non-breaking space
    :trim:
.. |-| unicode:: U+202F .. Thin non-breaking space
    :trim:

This project originated when I was learning digital filter design from
the book "Digital Signal Processing" [1]_ recommended to me by a
colleague.

The main idea here is the optimization of digital filters (with
additional constraints on group delay variation) with Differential
Evolution (DE) inspired by an early paper on the subject by Rainer Storn
[2]_, [3]_.

It also includes various Jupyter notebooks where I was
experimenting with what I'd learned. These include:

- IIR_Filter.ipynb: Various filter examples I could get my hands on to
  test my implementations of pole-zero plots, frequency response and
  group delay. It also includes the outcome of my attempts at
  optimizing filters with Differential Evolution (DE) inspired by an
  early paper on the subject by Rainer Storn [2]_ (the paper is behind a
  paywall, you may want to read the technical report [3]_ which has all
  information in the paper and is available online `from ICSI`_)
- Experiments.ipynb: Here I tried conversion of analog filters to their
  digital counterparts. In addition I was experimenting with a method
  for minimizing group delay variance.
- RIAA.ipynb: This has experiments with various digital filters for the
  RIAA equalization used in vinyl players. The digital filter can never
  fully match the analog filter (although I'm sure nobody my age can
  ever hope to hear the difference). This analyzes RIAA implementations
  from various sources.

Example call
------------

::

    mpirun --machinefile ~/.mpi-openmpi-cat  --np 8 \
    python3 -m filter_optimizer.filter_optimizer
    -u 0,0.04938,0.01,0.025,9 -u 0.04938,0.2716,0.025,0.025,73
    -u 0.2716,0.3334,0.05,0.05,151 -u 0.3334,0.395,-12,-12,43
    -u 0.395,0.5,-40,-40,37
    -l 0.0,0.04938,-0.01,-0.025,9 -l 0.04938,0.2716,-0.025,-0.025,43
    -l 0.2716,0.284,-0.05,-0.05
    -U 0.0,0.284,0.10125,0.30375,17 -L 0.0,0.284,-0.10125,-0.30375,17 -R1
    >! byparam.out

::

    mpirun --machinefile ~/.mpi-openmpi-cat  --np 8 filter-optimizer -P
    7 -Z 7 -u 0,1,-70,-70,100 -u 1,1.5,2.5,2.5,100
    -l1.5,3.14159265,-0.075,-0.075,31,1 -u
    1.5,3.14159265,0.075,0.075,31,1 -L 1.5,3.14159265,-1.25,-1.25,100 -U
    1.5,3.14159265,1.25,1.25,100 --dont-scale-by-pi -R2 >! 02vond.out

::

    mpirun --machinefile ~/.mpi-openmpi-cat  --np 8 filter-optimizer -P
    7 -Z 7 -u 0,1,-70,-70,100,0,0.9542 -u 1,1.5,2.5,2.5,100
    -l1.5,3.14159265,-0.075,-0.075,31,1 -u
    1.5,3.14159265,0.075,0.075,31,1 -L 1.5,3.14159265,-1.25,-1.25,100 -U
    1.5,3.14159265,1.25,1.25,100 --dont-scale-by-pi -R2 >! 02vond+1x.out

::

    mpirun --machinefile ~/.mpi-openmpi-cat  --np 8 filter-optimizer -P
    7 -Z 7 -u 0,1,-70,-70,100 -u 1,1.5,0.075,0.075,100,0,1.174
    -l1.5,3.14159265,-0.075,-0.075,31,1 -u
    1.5,3.14159265,0.075,0.075,31,1 -L 1.5,3.14159265,-1.25,-1.25,100 -U
    1.5,3.14159265,1.25,1.25,100 --dont-scale-by-pi -R8 >!
    hi-constraint-8+1.out

.. [1] John G. Proakis and Dimitris G. Manolakis. Digital Signal
    Processing: Principles, Algorithms, and Applications. Pearson
    Prentice Hall, Upper Saddle River, New Jersey, fourth edition, 2007.
.. [2] Rainer Storn. Differential evolution design of an IIR-filter. In
    IEEE International Conference on Evolutionary Computation (ICEC),
    pages 268–273, Nagoya, Japan, May 1996.
.. [3] Rainer Storn. Differential evolution design of an IIR-filter with
    requirements for magnitude and group delay. Technical Report
    TR-95-026, International Computer Science Institute (ICSI), June 1995.
    Available online `from ICSI`_ |--| as of this writing the links
    seems to be down.

.. _`from ICSI`:
    http://www.icsi.berkeley.edu/ftp/global/pub/techreports/1995/tr-95-026.pdf

