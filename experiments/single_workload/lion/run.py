#!/usr/bin/env python

import sys
sys.path.append('../../')
import evaluate
import config

dynamic_workload = {
    'fname': 'lion', 
    'pickle': config.workloadsdir + 'tsig.pickle',
    'numeval': 1000}
static_workloads = []

evaluate.bigeval(
	sig_names=['LCS', 'BayesAnd', 'LCSeq', 'Bayes2'],
	training_streams=config.traces[53]['training'],
	fpos_eval_streams=config.traces[53]['eval'],
	fpos_eval_count='5000000',
	dynamic_workload=dynamic_workload,
	static_workloads=static_workloads,
	dynamic_range=range(2,10)+range(10,50,5)+range(50,101,10),
	trials=5
)
