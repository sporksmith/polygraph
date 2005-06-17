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

%module pysary
%{
#include <sary/saryer.h>
#include <glib.h>
#include <sary/mmap.h>
#include <sary/text.h>
#include <sary/i.h>
#include <sary/saryconfig.h>
%}

typedef char gchar;
typedef int gboolean;
typedef int SaryInt;
extern Saryer*         saryer_new                      (const gchar
                                                 *file_name);
extern Saryer*         saryer_new2                     (const gchar *file_name,
                                                 const gchar *array_name);
extern void            saryer_destroy                  (Saryer *saryer);
extern gboolean        saryer_search                   (Saryer *saryer,
                                                 const gchar *pattern);
extern gboolean        saryer_search2                  (Saryer *saryer,
                                                 const gchar *pattern,
                                                 SaryInt len);
extern gboolean        saryer_isearch                  (Saryer *saryer,
                                                 const gchar *pattern,
                                                 SaryInt len);
extern void            saryer_isearch_reset            (Saryer *saryer);
extern gboolean        saryer_icase_search             (Saryer *saryer,
                                                 const gchar *pattern);
extern gboolean        saryer_icase_search2            (Saryer *saryer,
                                                 const gchar *pattern,
                                                 SaryInt len);
extern SaryText*       saryer_get_text                 (Saryer *saryer);
extern SaryMmap*       saryer_get_array                (Saryer *saryer);
SaryInt         saryer_get_next_offset          (Saryer *saryer);
extern gchar*          saryer_get_next_line            (Saryer *saryer);
extern gchar*          saryer_get_next_line2           (Saryer *saryer,
                                                 SaryInt *len);
extern gchar*          saryer_get_next_context_lines   (Saryer *saryer,
                                                 SaryInt backward,
                                                 SaryInt forward);
extern gchar*          saryer_get_next_context_lines2  (Saryer *saryer,
                                                 SaryInt backward,
                                                 SaryInt forward,
                                                 SaryInt *len);
extern gchar*          saryer_get_next_tagged_region   (Saryer *saryer,
                                                 const gchar *start_tag,
                                                 const gchar *end_tag);
extern gchar*          saryer_get_next_tagged_region2  (Saryer *saryer,
                                                 const gchar *start_tag,
                                                 SaryInt start_tag_len,
                                                 const gchar *end_tag,
                                                 SaryInt end_tag_len,
                                                 SaryInt *len);
extern SaryText*       saryer_get_next_occurrence      (Saryer *saryer);
extern gchar*          saryer_peek_next_position       (Saryer *saryer);
extern SaryInt         saryer_count_occurrences        (Saryer *saryer);
extern void            saryer_sort_occurrences         (Saryer *saryer);
extern void            saryer_enable_cache             (Saryer *saryer);
