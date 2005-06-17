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

/* Needham Schroder <sp?> algorithm, modified to incoorporate a "gap"
 * penalty, where a "gap" is defined to include sequences of mismatched
 * characters. 
 * Also, uses a special GAP character to keep track of gaps in multiple
 * alignments.
 * author: James Newsome
 */
#ifndef SUBSEQ_H
#define SUBSEQ_H

static const short GAP = 256;

void subsequence(short *seq1, unsigned int seq1_len,
                   short *seq2, unsigned int seq2_len,
                   float gap_penalty, 
                   short **subseq, int *subseq_len);

short* string_to_buf(char *str, int len);

void print_buf(short* buf, int len);

#endif
