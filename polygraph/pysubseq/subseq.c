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

/* Smith-Waterman algorithm, modified to incoorporate a "gap"
 * penalty, where a "gap" is defined to include sequences of mismatched
 * characters. 
 * Also, uses a special GAP character to keep track of gaps in multiple
 * alignments.
 * author: James Newsome
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef char bool;
enum {false=0, true=1};
enum {UP=0, LEFT=1, DIAG=2};
static const int GAP = 256;

typedef struct {
//	int cost;
	float cost;
	char direction;
} cell;

/*
 * Performs Smith-Waterman sequence alignment.
 * 
 * seq1 and seq2 are strings where each character has been widened to
 * 16 bits. This allows us to have the special GAP character without
 * needing to reserve a byte value.
 *
 * *subseq is set to the resulting subsequence, or NULL if there was
 * an error.
 */
void subsequence(short *seq1, unsigned int seq1_len,
                   short *seq2, unsigned int seq2_len,
                   float gap_penalty,
                   short **subseq, int *subseq_len)
{
	cell **matrix;
	int i,j;
//	int match_bonus = 100;
//	int gap_penalty_i = (int)(gap_penalty*match_bonus);

	*subseq_len = 0;
	*subseq = NULL;

	/* allocate the cost matrix. */
	matrix = (cell**) malloc((seq1_len + 1) * sizeof(cell*));
	if (matrix == NULL)
		return;
	for (i=0; i < seq1_len+1; i++) {
		matrix[i] = (cell*)malloc((seq2_len+1)*sizeof(cell));
		if (matrix[i] == NULL) {
			/* cleanup */
			for(j = 0; j<i; j++) {
				free(matrix[j]);
			}
			free(matrix);
			return;
		}
	}

	/* initialize costs to zero */
	for(i = 0; i < (seq1_len+1); i++) {
		matrix[i][0].cost = 0;
	}
	for(i = 0; i < (seq2_len+1); i++) {
		matrix[0][i].cost = 0;
	}

	/* fill in the rest of the matrix */
	for(i = 1; i < (seq1_len+1); i++) {
		for(j = 1; j < (seq2_len+1); j++) {
			float Dcost, Lcost, Ucost;
			
			/* compute diagonal cost */
			Dcost = matrix[i-1][j-1].cost;
			if (seq1[i-1] == seq2[j-1] && seq1[i-1] != GAP)
				Dcost += 1.0;
			else if (i > 1 && j > 1 && seq1[i-2] == seq2[j-2])
				Dcost -= gap_penalty;
			matrix[i][j].cost = Dcost;
			matrix[i][j].direction = DIAG;

			/* compute left cost */
			Lcost = matrix[i][j-1].cost;
			if (j > 1 && seq1[i-1] == seq2[j-2])
				Lcost -= gap_penalty;
			if (Lcost > matrix[i][j].cost) {
				matrix[i][j].cost = Lcost;
				matrix[i][j].direction = LEFT;
			}

			/* compute up cost */
			Ucost = matrix[i-1][j].cost;
			if (i > 1 && seq1[i-2] == seq2[j-1])
				Ucost -= gap_penalty;
			if (Ucost > matrix[i][j].cost) {
				matrix[i][j].cost = Ucost;
				matrix[i][j].direction = UP;
			}

//			printf("%f ", matrix[i][j].cost);
		}
	}


	/* one traceback to find length of subsequence */
	i = seq1_len;
	j = seq2_len;
	bool last_was_match = false;
//	printf("%f\n", matrix[i][j].cost);
	while (i > 0 && j > 0) {
		if (matrix[i][j].direction == DIAG) {
			/* diagonal. add 1 if it's a match */
			if (seq1[i-1] == seq2[j-1] && seq1[i-1] != GAP) {
				(*subseq_len)++;
				last_was_match = true;
			} else {
				if (last_was_match) {
					(*subseq_len)++;
				}
				last_was_match = false;
			}
			i--;
			j--;
		} else if (matrix[i][j].direction == LEFT) {
			/* add 1 for start of a gap */
			if (last_was_match) {
				(*subseq_len)++;
			}
			last_was_match = false;

			j--;
		} else {
			/* add 1 for start of a gap */
			if (last_was_match) {
				(*subseq_len)++;
			}
			last_was_match = false;

			i--;
		}
	}

	*subseq = (short*) malloc((*subseq_len) * sizeof(short));

	/* now fill in the subsequence */
	i = seq1_len;
	j = seq2_len;
	int offset = *subseq_len - 1;
	last_was_match = false;
	while (i > 0 && j > 0) {
		if (matrix[i][j].direction == DIAG) {
			/* is this cell a match? */
			if (seq1[i-1] == seq2[j-1] && seq1[i-1] != GAP) {
				(*subseq)[offset] = seq1[i-1];
				offset--;
				last_was_match = true;
			} else {
				if (last_was_match) {
					(*subseq)[offset] = GAP;
					offset--;
				}
				last_was_match = false;
			}

			i--;
			j--;
		} else if (matrix[i][j].direction == LEFT) {
			if (last_was_match) {
				/* gap */
				(*subseq)[offset] = GAP;
				offset--;
			}
			last_was_match = false;
			j--;
		} else {
			if (last_was_match) {
				/* gap */
				(*subseq)[offset] = GAP;
				offset--;
			}
			last_was_match = false;
			i--;
		}
	}

	/* free cost matrix */
	for (i=0; i < seq1_len+1; i++) {
		free(matrix[i]);
	}
	free(matrix);
}

short* string_to_buf(char *str, int len)
{
	short* buf;
	int i;

	buf = (short*)malloc(len * sizeof(short));
	for (i=0; i < len; i++) {
		buf[i] = str[i];
	}

	return buf;
}

void print_buf(short* buf, int len)
{
	int i;
	for (i=0; i < len; i++) {
		if(buf[i] == GAP) 
			printf("_");
		else
			printf("%c", (char)buf[i]);
	}
	printf("\n");
}
