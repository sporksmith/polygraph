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

def create_workload(generator, filename):
    import cPickle
    workload = [sample for sample in generator]

    f = open(filename, 'w')
    cPickle.dump(workload, f, cPickle.HIGHEST_PROTOCOL)
    f.close()

def create_noise_workload(tracefile, count, filename):
    # get total number of streams in the trace
    import polygraph.trace_crunching.stream_trace as stream_trace

    s = stream_trace.StreamTrace(tracefile)

    # select which streams to use
    import random
    indices = range(s.numstreams())
    random.shuffle(indices)
    indices = indices[:count]
    indices.sort()

    # get those streams
    workload = []
    for i in indices:
        s.seek(i)
        workload.append(s.next())

    if s.numstreams() < count:
        print '*' * 80
        print 'WARNING: Only %d streams in %s, need %d to' % \
                (s.numstreams(), tracefile, count)
        print 'generate noise workload. Will cludge by duplicating'
        print 'streams as necessary.'
        print '*' * 80
        workload *= (count / s.numstreams()) + 1
        workload = workload[:count]

    random.shuffle(workload)

    # write to file
    import cPickle
    f = open(filename, 'w')
    cPickle.dump(workload, f, cPickle.HIGHEST_PROTOCOL)
    f.close()

if __name__ == '__main__':
    # these should correspond to the largest workload needed
    trials=5
    dynamic_range=range(2,10)+range(10,50,5)+range(50,101,10)
    addtl = 1000
    number = trials * sum(dynamic_range) + addtl

    #http noise
    import sys
    sys.path.append('../')
    import config
    create_noise_workload(config.traces[80]['eval'], number,'http_noise.pickle')

    #dns noise
    create_noise_workload(config.traces[53]['eval'], number, 'dns_noise.pickle')

    #atphttpd workload
    import polygraph.worm_gen.atphttpd as atphttpd
    create_workload(atphttpd.ATPhttpd().generate(number), 'atphttpd.pickle')

    #apache knacker workload
    import polygraph.worm_gen.apache_host as apache_host
    create_workload(apache_host.ApacheHost().generate(number), 'apache.pickle')

    #lion (dns tsig) workload
    import polygraph.worm_gen.bindTSIG as bindTSIG
    create_workload(bindTSIG.bindTSIG().generate(number), 'tsig.pickle')

    #clet workload
    import polygraph.worm_gen.clet as clet
    create_workload(clet.Clet().generate(number), 'clet.pickle')

