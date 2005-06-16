#ifndef PG_SUTIL_H
#define PG_SUTIL_H

typedef char bool;
const bool True = 1;
const bool False = 0;

typedef struct {
	unsigned char *bits;
	unsigned int count;
} bitfield_t;

typedef struct {
        LST_StringSet *string_set;
        LST_STree *tree;
        int numstrings;
                                                                                
        /* annotation of which strings have 
	 * leaves below a particular node 
	 */
        annotation_t *annotations;
        bool annotated;
} tree_handle_t;


#endif
