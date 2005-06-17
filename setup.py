#!/usr/bin/env python
#      Polygraph (release 0.1)
#      Signature generation algorithms for polymorphic worms
#
#      Copyright (c) 2004-2005, Intel Corporation
#      All Rights Reserved
#
#  This software is distributed under the terms of the Eclipse Public
#  License, Version 1.0 which can be found in the file named LICENSE.
#  ANY USE, REPRODUCTION OR DISTRIBUTION OF THIS SOFTWARE CONSTITUTES
#  RECIPIENT'S ACCEPTANCE OF THIS AGREEMENT

# use pkgconfig to get directories for glib.
# Not sure how portable this is.
import os
(input, output) = os.popen2('pkg-config glib-2.0 --cflags')
line = output.readline()
dirs = []
for item in line.split():
    dirs.append(item[2:]) #chop off '-I'

from distutils.core import setup, Extension

setup(name="Polygraph",
      version="0.1",
      description="Automatic worm signature generation",
      author="James Newsome",
      author_email="jnewsome@ece.cmu.edu",
      url="http://www.ece.cmu.edu/~jnewsome",
      packages=['polygraph', 'polygraph.sigprob', 'polygraph.trace_crunching',\
                'polygraph.worm_gen', 'polygraph.sig_gen', 'polygraph.util'],
      ext_modules=[ \
          Extension('polygraph.util.pysubseqc', \
                    sources=['polygraph/pysubseq/pysubseqc.c', \
                             'polygraph/pysubseq/subseq.c']), \
          Extension('polygraph.util.sutilc', \
                    sources=['polygraph/sutil/sutilc.c'], \
                    libraries=['stree']),
          Extension('polygraph.util.pysary', \
                    sources=['polygraph/pysary/pysary_wrap.c'],\
                    libraries=['sary', 'gthread', 'glib', 'pthread'],\
                    include_dirs=dirs)
      ],
      scripts=['polygraph/bin/reconstruct_streams']
     )
