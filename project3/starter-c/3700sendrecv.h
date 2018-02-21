/*
 * CS3700, Spring 2015
 * Project 2 Starter Code
 */

#ifndef __3700SENDRECV_H__
#define __3700SENDRECV_H__

#include <stdio.h>
#include <stdarg.h>

typedef struct header_t {
  unsigned int magic:14;
  unsigned int ack:1;
  unsigned int eof:1;
  unsigned short length;
  unsigned int sequence;
} header;

unsigned int MAGIC;

void dump_packet(unsigned char *data, int size);
header *make_header(int sequence, int length, int eof, int ack);
header *get_header(void *data);
char *get_data(void *data);
char *timestamp();
void mylog(char *fmt, ...);

#endif

