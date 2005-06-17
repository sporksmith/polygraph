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
