print "*" * 80
print """WARNING: Using default training and evaluation innocuous traces.
These are trivial traces that are included only to verify that Polygraph
is correctly installed.
You should specify different traces in experiments/config.py"""
print "*" * 80

traces = {}
#prefix = '../../traces/'
prefix = '/home/jnewsome/project/polysig/polygraph_dist/experiments/traces/' 
workloadsdir = '../../workloads/'
traces[80] = {'training': prefix + 'training.80.streams',
              'eval': prefix + 'eval.80.streams'}

traces[53] = {'training': prefix + 'training.53.streams',
              'eval': prefix + 'eval.53.streams'}

