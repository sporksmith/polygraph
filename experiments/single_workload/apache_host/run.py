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

import sys
sys.path.append('../../')
import evaluate
import config

dynamic_workload = {
        'fname': 'apache', 
        'pickle': config.workloadsdir + 'apache.pickle',
        'numeval': 1000,
}

static_workloads = []

evaluate.bigeval(
    sig_names=['LCS', 'BayesAnd', 'LCSeq', 'Bayes2'],
	training_streams=config.traces[80]['training'],
	fpos_eval_streams=config.traces[80]['eval'],
	fpos_eval_count='5000000',
	dynamic_workload=dynamic_workload,
	static_workloads=static_workloads,
	dynamic_range=range(2,10)+range(10,50,5)+range(50,101,10),
#	dynamic_range=range(20)+range(20,101,10),
	trials=5
)
