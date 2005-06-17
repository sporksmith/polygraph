/*
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
*/

#include <libstree.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <Python.h>

typedef char bool;
const bool True = 1;
const bool False = 0;

typedef struct {
	LST_StringSet *string_set;
	LST_STree *tree;
	int numstrings;
	bool annotated;
} tree_handle_t;

/*
typedef struct {
	char *buf;
	int len;
} string_t;
*/

typedef struct {
	/* input parameters for callback */
	bool save_annotations;
	int min_len;
	int min_occ;
	tree_handle_t *tree;
	/* output parameters */
	PyObject *substrings;
} params_t;

typedef struct {
	int *strings;
} annotation_t;

/* returns a dictionary mapping the strings that this substring
 * occurred in to the number of times it occurred in each string
 */
static 
PyObject* subtree_occurrences(LST_Node *node, int numstrings)
{
	assert(node != NULL);
	PyObject *pydict = PyDict_New();

	if(node == NULL)
		return pydict;

	int i;
	annotation_t *annotation = (annotation_t*)node->annotation;
	for(i=0; i<numstrings; i++) {
		if(annotation->strings[i]) {
			PyObject *index, *count;
			index = PyInt_FromLong(i);
			count = PyInt_FromLong(annotation->strings[i]);
			PyDict_SetItem(pydict, index, count);
			Py_DECREF(index);
			Py_DECREF(count);
		}
	}

	return pydict;
}

/* callback to free the annotations */
int clear_annotations(LST_Node *node, void *p)
{
	annotation_t *annotation;
	annotation = (annotation_t*)node->annotation;
	if (annotation != NULL) {
		free(annotation->strings);
		free(annotation);
		node->annotation = NULL;
//		printf("Freeing annotation!\n");
	}

	return 1;
}

/* callback for tree traversal.
 * annotates nodes to keep track of which strings
 * have leaves in its subtree.
 */
int annotate(LST_Node *node, params_t *p)
{
	annotation_t *annotation;
	annotation_t *child_annotation;
	LST_Edge *edge;
	LST_Node *child;
	int i;

	/* allocate annotation for this node */
	if (node->annotation == NULL) {
		node->annotation = malloc(sizeof(annotation_t));
		assert(node->annotation != NULL);
		annotation = (annotation_t*)node->annotation;
		annotation->strings = (int*)calloc(p->tree->numstrings, sizeof(int));	
		assert(annotation->strings != NULL);
	} else {
		/* reallocate in case number of strings has changed */
		annotation = (annotation_t*)node->annotation;
//		annotation->strings = realloc(annotation->strings,
//					p->tree->numstrings * sizeof(int));
		free(annotation->strings);
		annotation->strings = (int*)calloc(p->tree->numstrings, sizeof(int));
		assert(annotation->strings != NULL);
	}

	/* initialize the strings annotation */
	bzero(annotation->strings, (p->tree->numstrings)*sizeof(int));

	if (lst_node_is_leaf(node)) {
		annotation->strings[lst_stree_get_string_index(p->tree->tree, node->up_edge->range.string)] = 1;
		return True;
	} 

	/* incoorporate children's annotations */
	for (edge = node->kids.lh_first; edge; edge = edge->siblings.le_next) {
		child = edge->dst_node;
		assert(child->annotation != NULL);
		child_annotation = (annotation_t*)child->annotation;
		
		for(i=0; i<p->tree->numstrings; i++) {
//			annotation->strings[i] = annotation->strings[i] || child_annotation->strings[i];
			annotation->strings[i] += child_annotation->strings[i];
		}

		if (!p->save_annotations) {
			free(child_annotation->strings);
			free(child_annotation);
			child->annotation = NULL;
		}
	}

	/* how many strings have this substring? */
	int string_count = 0;
	int occ_count = 0;
//	LST_String *s = lst_node_get_string(node, 1000);
//	printf("%s: ", lst_string_print(s));
	for(i=0; i<p->tree->numstrings; i++) {
//		printf("%d, ", annotation->strings[i]);
		if(annotation->strings[i]) {
			occ_count += annotation->strings[i];
			string_count++;
		}
	}
//	printf(": %d %d\n", occ_count, string_count);

	/* if this node's substring occurs in min_occ strings,
	 * and is at least min_len long, report it.
	 */
	if (string_count >= p->min_occ) {
		int len = lst_node_get_string_length(node);
		if (len >= p->min_len) {
			/* add a dictionary mapping the strings that this
			 * substring occurred in to the number of times
			 * it occurred in each string.
			 */
			PyObject *pydict = subtree_occurrences(node,p->tree->numstrings);

			LST_String *s = lst_node_get_string(node, len);
//			printf("adding %s\n", (char*)s->data);
			PyObject *pystring = 
				PyString_FromStringAndSize(s->data, s->num_items-1);

			PyDict_SetItem(p->substrings, pystring, pydict);
			Py_DECREF(pystring);
			Py_DECREF(pydict);
//			printf("%s\n", lst_string_print(s));
			lst_string_free(s);
		}
	}

	return True;
}

/* copied from stree library internals */
static LST_Edge *
node_find_edge_with_startitem(LST_Node *node, LST_String *string, u_int index)
{
  LST_Edge *edge = NULL;

  if (!node || !string || index >= string->num_items)
    {
      return NULL;
    }

  for (edge = node->kids.lh_first; edge; edge = edge->siblings.le_next)
    {
      /* Skip this edge if the first characters don't match
       * what we're looking for.
       */
      if (lst_string_eq(edge->range.string, edge->range.start_index,
                        string, index))
        return edge;
    }

  return NULL;
}

/* copied from stree library internals (and modified) */
static LST_Node*
stree_find_string(LST_STree *tree, LST_String *string)
{
  LST_Edge   *edge = NULL;
  u_int       items_todo = 0, items_done = 0, common;
  LST_Node   *node;

  if (!tree || !string)
    {
      return NULL;
    }

  node = tree->root_node;
  items_todo = string->num_items - 1; /* don't match terminator */

  /* Find edge where our string starts, making use of the fact
   * that no two out-edges from a node can start with the same
   * character.
   */
  while (items_todo > 0)
    {
      edge = node_find_edge_with_startitem(node, string, items_done);
//      printf("edge is %d to %d\n", edge->src_node->id, edge->dst_node->id);
//      printf("left to match: %d\n", items_todo);

      if (!edge)
        {
//          printf("didn't find edge\n");
          return NULL;
        }

      common =
        lst_string_items_common(edge->range.string, edge->range.start_index,
                                string, items_done,
                                items_todo);


      if (common < (u_int) lst_edge_get_length(edge))
        {
	      if (common == items_todo){
//		printf("found in edge, returning node %d\n", edge->dst_node->id);
		return edge->dst_node;
	      }

//          printf("mismatch in edge\n");
          return NULL;
        }

      node = edge->dst_node;
      items_done += lst_edge_get_length(edge);
      items_todo -= lst_edge_get_length(edge);
    }

//  printf("found at node %d\n", edge->dst_node->id);
  return edge->dst_node;
}

/*
 * Here, tree is made up of tokens, and we're returning
 * which tokens are contained in search string.
 * Naive implementation for now- can make this linear time.
 */
static PyObject*
stree_find_tokens(LST_STree *tree, LST_String *string)
{
	int pos = 0;
	int offset = 0;
	int common = 0;
	int length = lst_string_get_length(string);
	int skip = 0;
	
	LST_Node *node = tree->root_node;
	LST_Edge   *edge = NULL;
	LST_Edge   *c_edge = NULL;
	LST_String *longest_match = NULL;
	PyObject *pydict = PyDict_New();

	for(pos=0; pos < length; pos++) {
		longest_match = NULL;
		while(1) {
//			printf("pos %d offset %d\n", pos, offset);

			/* if any out-edges are the end of a string, mark this as our best
			 * match so far.
			 */
			for (c_edge = node->kids.lh_first; c_edge; c_edge = c_edge->siblings.le_next) {
				if(c_edge->range.start_index == 
				   lst_string_get_length(c_edge->range.string) &&
//				   lst_node_get_string_length(node) ==
				   offset ==
				   lst_string_get_length(c_edge->range.string))
					longest_match = c_edge->range.string;
			}

			edge = node_find_edge_with_startitem(node, string, pos+offset);
			if (!edge) {
				/* mismatch */
//				printf("No matching child edge\n");
				common = 0;
				break;
			}

			if (skip >= lst_edge_get_length(edge)) {
				common = lst_edge_get_length(edge);
				skip -= common;
//				printf("skipping edge of length %d\n", lst_edge_get_length(edge));
			} else {
//				printf("matching edge from byte %d\n", skip);
				common = skip + lst_string_items_common(edge->range.string,
								 edge->range.start_index + skip,
								 string, pos+offset+skip,
								 lst_edge_get_length(edge)-skip);
	//			printf("Matched %d characters\n", common);
				skip = 0;
			}
							 
			if (common < (u_int) lst_edge_get_length(edge)) {
				/* mismatch in edge */
//				printf("Mismatch in edge\n");
				if (edge->range.start_index + common == 
				    lst_string_get_length(edge->range.string) &&
//				    lst_node_get_string_length(node) + common ==
				    offset + common ==
				    lst_string_get_length(edge->range.string)) {
					longest_match = edge->range.string;
				}

				break;
			}

			node = edge->dst_node;
			offset += lst_edge_get_length(edge);
		}

		if (longest_match != NULL) {
			PyObject *pyindex = PyInt_FromLong(pos);
			PyObject *pystring = PyInt_FromLong(lst_stree_get_string_index(tree, longest_match));
			PyDict_SetItem(pydict, pyindex, pystring);
			Py_DECREF(pyindex);
			Py_DECREF(pystring);
//			printf("%d %s\n", pos, lst_string_print(longest_match));
		}

		/* XXX change this to follow suffix links and
		 * do skip/count to achieve linear time bound 
		 */

		skip = offset + common - 1;
		skip = (skip < 0 ? 0 : skip);
		node = tree->root_node;
		offset = 0;

/*
		if (node->suffix_link_node != NULL) {
			node = node->suffix_link_node;
			offset = lst_node_get_string_length(node);
//			printf("Following suffix link to depth %d\n", offset);
		} else {
			node = tree->root_node;
			offset = 0;
		}
*/

	}
	return pydict;
}

static PyObject*
st_create(PyObject* self, PyObject* args)
{
	PyObject *pylist = NULL, *pystring = NULL;
	char *cstring = NULL;
	int length;
	tree_handle_t *handle;
	LST_String *string;

	/* parse arguments */
	if (!PyArg_ParseTuple(args, "O:st_create", &pylist)) return NULL;

	/* create the tree */
	handle = malloc(sizeof(tree_handle_t));
	if (handle == NULL) {
		return PyErr_NoMemory();
	}
	handle->tree = lst_stree_new(NULL);
	assert(handle != NULL);

	/* fill in the tree and stringset */
	PyObject *iterator = PyObject_GetIter(pylist);
	handle->string_set = lst_stringset_new();
	assert(handle->string_set != NULL);
	handle->numstrings = 0;
	while((pystring = PyIter_Next(iterator)) != NULL) {
		handle->numstrings++;
		if (PyString_AsStringAndSize(pystring,&cstring,&length)) {
			Py_DECREF(iterator); 
			lst_stree_free(handle->tree);
			lst_stringset_free(handle->string_set);
			free(handle);
			return NULL;
		}
		/* LST_String is pointing back at the python string's data.
		 * python wrapper class keeps a reference to each string added,
		 * so don't keep the reference here.
		 */
		Py_DECREF(pystring);

		/* this is freed when stringset is freed */
		string = (LST_String*)malloc(sizeof(LST_String));
		if (string == NULL) {
			Py_DECREF(iterator); 
			lst_stree_free(handle->tree);
			lst_stringset_free(handle->string_set);
			free(handle);
			return PyErr_NoMemory();
		}
		lst_string_init(string, cstring, 1, length);
		lst_stringset_add(handle->string_set, string);
		lst_stree_add_string(handle->tree, string);
	}
	Py_DECREF(iterator);
	iterator = NULL;

	/* not annotated */
	handle->annotated = False;

//	lst_debug_print_tree(handle->tree);

	/* return pointer to the handle */
	return Py_BuildValue("l", (long)handle);
}

static PyObject*
st_add(PyObject* self, PyObject* args)
{
	tree_handle_t *handle;
	LST_String *lststring;
	char *cstring;
	long length;

	if (!PyArg_ParseTuple(args, "ls#:st_add", (long*)&handle, &cstring, &length)) return NULL;

	lststring = (LST_String*)malloc(sizeof(LST_String));
	if (lststring == NULL) {
		return PyErr_NoMemory();
	}
	lst_string_init(lststring, cstring, 1, length);
	lst_stringset_add(handle->string_set, lststring);
	lst_stree_add_string(handle->tree, lststring);

	handle->numstrings++;

	/* Invalidate current annotations */
	if(handle->annotated) {
		lst_alg_bus(handle->tree, (LST_NodeVisitCB)clear_annotations, NULL);
		handle->annotated = False;
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject*
st_destroy(PyObject* self, PyObject* args)
{
	tree_handle_t *handle;

	if (!PyArg_ParseTuple(args, "l:st_destroy", (long*)&handle)) return NULL;

	lst_alg_bus(handle->tree, (LST_NodeVisitCB)clear_annotations, NULL);
	lst_stree_free(handle->tree);
	handle->tree = NULL;
	lst_stringset_free(handle->string_set);
	handle->string_set = NULL;
	free(handle);
	Py_INCREF(Py_None);
	return Py_None;
}

/*
 * strings: a list of strings, terminated with a null pointer.
 * min_len: minimum length of common substrings to report
 * min_occ: minimum number of strings that a substring occurs in
 */
PyObject* common_sub(tree_handle_t *tree, int min_len, int min_occ, bool save_annotations)
{
	params_t p;

	p.tree = tree;
	p.save_annotations = save_annotations;
	p.min_len = min_len;
	p.min_occ = min_occ;
	p.substrings = PyDict_New();
	lst_alg_bus(tree->tree, (LST_NodeVisitCB)annotate, &p);
//	lst_alg_dfs(tree->tree, (LST_NodeVisitCB)annotate, &p);
	tree->annotated = save_annotations;

	return p.substrings;
}

static PyObject*
st_find(PyObject* self, PyObject* args)
{
	tree_handle_t *handle;
	char *string = NULL;
	long length = 0;
	LST_String string_obj;
	LST_Node *node;

	if (!PyArg_ParseTuple(args, "ls#:st_find", (long*)&handle, &string, &length)) return NULL;

	lst_string_init(&string_obj, string, 1, length);

	if (!handle->annotated) {
		//FIXME: should separate annotation functionality.
		// currently, set parameters so nothing is returned
//		PyObject *p = common_sub(handle, 1, 1);
		PyObject *p = common_sub(handle, 1, handle->numstrings+1, True);
		Py_DECREF(p);
	}

	node = stree_find_string(handle->tree, &string_obj);

	return subtree_occurrences(node, handle->numstrings);
}

static PyObject*
py_find_tokens(PyObject* self, PyObject* args)
{
	tree_handle_t *handle;
	char *string = NULL;
	long length = 0;
	LST_String string_obj;

	if (!PyArg_ParseTuple(args, "ls#:st_find", (long*)&handle, &string, &length)) return NULL;
	lst_string_init(&string_obj, string, 1, length);

	return stree_find_tokens(handle->tree, &string_obj);
}

/*
int main(int argc, char **argv)
{
	int i;
	string_t *strings = malloc((argc-1) * sizeof(string_t));
	assert(strings != NULL);
	for(i=1; i < argc; i++) {
		strings[i-1].buf = argv[i];
		strings[i-1].len = strlen(argv[i]);
	}

	common_sub(strings, argc-1, 2, 2);
	return 0;
}
*/

static PyObject*
common_substrings(PyObject* self, PyObject* args)
{
	int min_len, min_occ;
	tree_handle_t *handle;

	if (!PyArg_ParseTuple(args, "lii:common_substrings", (long*)&handle, &min_len, &min_occ)) return NULL;


	return common_sub(handle, min_len, min_occ, False);
}

static PyMethodDef sutil_funcs[] = {
	{"common_substrings", (PyCFunction)common_substrings, METH_VARARGS, "fillmein"},
	{"st_create", (PyCFunction)st_create, METH_VARARGS, "fillmein"},
	{"st_destroy", (PyCFunction)st_destroy, METH_VARARGS, "fillmein"},
	{"st_find", (PyCFunction)st_find, METH_VARARGS, "fillmein"},
	{"py_find_tokens", (PyCFunction)py_find_tokens, METH_VARARGS, "fillmein"},
	{"st_add", (PyCFunction)st_add, METH_VARARGS, "fillmein"},
	{NULL}
};

void initsutilc(void)
{
	Py_InitModule3(
		"sutilc", 
		sutil_funcs,
		"String utilities module. Don't use this directly. Use sutil instead.");
}
