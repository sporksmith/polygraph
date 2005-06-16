#include <Python.h>
#include "subseq.h"

static short* sequence_to_buf(PyObject *seq)
{
	int len = PySequence_Size(seq);
	short* buf = (short*)malloc(len * sizeof(short));
	int i;

	PyObject *litem;
	for(i=0; i < len; i++) {
		litem = PySequence_GetItem(seq, i);
		buf[i] = (short)PyInt_AsLong(litem);
		Py_DECREF(litem);
	}
	return buf;
}

static PyObject*
buf_to_list(short* buf, int length)
{
	int i;
	PyObject *list;

	list = PyList_New(length);

	for(i=0; i < length; i++) {
		PyList_SET_ITEM(list, i, PyInt_FromLong(buf[i]));
	}

	return list;
}

static PyObject*
py_lcseq(PyObject* self, PyObject* args)
{
	float gap_penalty;
	PyObject *pyseq1, *pyseq2, *pysubseq;
	short *seq1, *seq2;
	short *subseq;
	int subseq_len;

	if (!PyArg_ParseTuple(args, "OOf:common_substrings", &pyseq1, &pyseq2, &gap_penalty)) return NULL;
	
	seq1 = sequence_to_buf(pyseq1);
	seq2 = sequence_to_buf(pyseq2);

	subsequence(seq1, PySequence_Size(pyseq1),
                   seq2, PySequence_Size(pyseq2),
                   gap_penalty, 
                   &subseq, &subseq_len);
	pysubseq = buf_to_list(subseq, subseq_len);
	free(subseq);
	free(seq1);
	free(seq2);

	return pysubseq;
}

static PyMethodDef pysubseqc_funcs[] = {
	{"lcseq", (PyCFunction)py_lcseq, METH_VARARGS, "fillmein"},
	{NULL}
};

void initpysubseqc(void)
{
	Py_InitModule3(
		"pysubseqc", 
		pysubseqc_funcs,
		"python interface to libpolygraph"
	);
}
