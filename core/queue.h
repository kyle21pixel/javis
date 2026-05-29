#ifndef JAVIS_QUEUE_H
#define JAVIS_QUEUE_H

#include <stdint.h>
#include <stddef.h>

#ifdef _WIN32
  #define JAVIS_API __declspec(dllexport)
#else
  #define JAVIS_API __attribute__((visibility("default")))
#endif

#define QUEUE_CAPACITY 1024
#define MAX_MSG_LEN    4096

typedef struct {
    char   channel[32];   /* "email" | "sms" | "chat" */
    char   sender[256];
    char   subject[512];
    char   body[MAX_MSG_LEN];
    int64_t timestamp;
    int    processed;     /* 0 = pending, 1 = done */
} JavisMessage;

typedef struct {
    JavisMessage  buffer[QUEUE_CAPACITY];
    volatile int  head;
    volatile int  tail;
    volatile int  count;
} JavisQueue;

/* Lifecycle */
JAVIS_API JavisQueue* queue_create(void);
JAVIS_API void        queue_destroy(JavisQueue* q);

/* Operations */
JAVIS_API int         queue_push(JavisQueue* q, const JavisMessage* msg);
JAVIS_API int         queue_pop(JavisQueue* q, JavisMessage* out);
JAVIS_API int         queue_size(JavisQueue* q);
JAVIS_API int         queue_is_empty(JavisQueue* q);
JAVIS_API int         queue_is_full(JavisQueue* q);

#endif /* JAVIS_QUEUE_H */
