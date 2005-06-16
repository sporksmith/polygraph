#!/usr/bin/env python

def median(l):
    l = l[:]
    l.sort()
    return l[len(l)/2]

def get_median(prefix):
    trial=0
    data = {}
    while True:
        try:
            f = open('%s.%d' % (prefix,trial))
        except IOError:
            break
        for line in f.xreadlines():
            (x,y) = line.split()
            x = int(x)
            y = float(y)
            if not data.has_key(x):
                data[x] = []
            data[x].append(y)
        trial += 1

    xs = data.keys()
    xs.sort()
    rv = {}
    for x in xs:
        rv[x] = median(data[x])
    return rv

# algorithms = list of {'pname': '', 'fname': ''}
# workloads = list of {'pname': '', 'fname': ''}
def make_table(algorithms, all_workloads, ts, xs):
    workloads = []
    for w in all_workloads:
        if w['numeval'] > 0:
            workloads.append(w)



    if ts:
        ts = ts + '.'
    else:
        ts = ''
    print ts
    # get the median false positive and negatives
    medians = {}
    for alg in algorithms:
        medians[alg] = {}
        medians[alg]['fp'] = get_median('%s%s.fpos' % (ts, alg.fname))

        medians[alg]['fn'] = {}
        for work in workloads:
            if work['numeval'] > 0:
                medians[alg]['fn'][work['fname']] = get_median('%s%s.fneg.%s' % (ts, alg.fname, work['fname']))

    # build the table
    result = []
    result.append('\\begin{table*}\n')
    result.append('\\begin{center}\n')
    result.append('\\begin{tabular}{|c|')
    result.append(('|c' * (len(workloads)+1) + '|') * len(algorithms))
    result.append('}\\hline\n')
    
    # Algorithm names along the top
    for i in xrange(len(algorithms)):
        if i < len(algorithms)-1:
            result.append('& \multicolumn{2}{c||}{%s} ' % algorithms[i].pname)
        else:
            result.append('& \multicolumn{2}{c|}{%s} ' % algorithms[i].pname)
    result.append(r'\\' + '\n')
    result.append('\\hline\n')
    result.append('Samples ')
    result.append(('& False Pos ' + '& False Neg' * len(workloads)) * len(algorithms)) 
    result.append(r'\\' + '\n')
    result.append('\\hline\n')

    for x in xs:
        result.append('%d ' % x)
        for alg in algorithms:
            result.append("& %f " % medians[alg]['fp'][x])
            for work in workloads:
                if work['numeval'] > 0:
                    result.append("& %f " % medians[alg]['fn'][work['fname']][x])
        result.append(r'\\' + '\n')

    result.append('\\hline\n')
    result.append('\\end{tabular}\n')
    result.append('\\end{center}\n')
    result.append('\\end{table*}\n')

    return ''.join(result)
