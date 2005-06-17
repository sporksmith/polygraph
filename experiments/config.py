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

print "*" * 80
print """WARNING: Using default training and evaluation innocuous traces.
These are trivial traces that are included only to verify that Polygraph
is correctly installed.
You should specify different traces in experiments/config.py"""
print "*" * 80

traces = {}

# change this!
experiments_dir='/home/jnewsome/project/polysig/polygraph_dist/experiments/'

prefix = experiments_dir + 'traces/'
workloadsdir = experiments_dir + 'workloads/'
traces[80] = {'training': prefix + 'training.80.streams',
              'eval': prefix + 'eval.80.streams'}

traces[53] = {'training': prefix + 'training.53.streams',
              'eval': prefix + 'eval.53.streams'}

