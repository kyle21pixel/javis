/*
 * J.A.V.I.S. Message Queue - Lock-free Ring Buffer (C Implementation)
 * High-throughput message routing between channels and the AI brain.
 */

#include "queue.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
  #include <windows.h>
  #define ATOMIC_INC(x) InterlockedIncrement((LONG volatile*)&(x))
  #define ATOMIC_DEC(x) InterlockedDecrement((LONG volatile*)&(x))
  #define MEMORY_BARRIER() MemoryBarrier()
#else
  #define ATOMIC_INC(x) __sync_fetch_and_add(&(x), 1)
  #define ATOMIC_DEC(x) __sync_fetch_and_sub(&(x), 1)
  #define MEMORY_BARRIER() __sync_synchronize()
#endif

JAVIS_API JavisQueue* queue_create(void) {
    JavisQueue* q = (JavisQueue*)calloc(1, sizeof(JavisQueue));
    if (!q) return NULL;
    q->head  = 0;
    q->tail  = 0;
    q->count = 0;
    return q;
}

JAVIS_API void queue_destroy(JavisQueue* q) {
    if (q) free(q);
}

JAVIS_API int queue_push(JavisQueue* q, const JavisMessage* msg) {
    if (!q || !msg) return -1;
    if (q->count >= QUEUE_CAPACITY) return -1; /* Full */

    int pos = q->tail % QUEUE_CAPACITY;
    memcpy(&q->buffer[pos], msg, sizeof(JavisMessage));
    q->buffer[pos].timestamp = (int64_t)time(NULL);
    q->buffer[pos].processed = 0;

    MEMORY_BARRIER();
    q->tail = (q->tail + 1) % QUEUE_CAPACITY;
    ATOMIC_INC(q->count);
    return 0;
}

JAVIS_API int queue_pop(JavisQueue* q, JavisMessage* out) {
    if (!q || !out) return -1;
    if (q->count <= 0) return -1; /* Empty */

    int pos = q->head % QUEUE_CAPACITY;
    memcpy(out, &q->buffer[pos], sizeof(JavisMessage));
    memset(&q->buffer[pos], 0, sizeof(JavisMessage));

    MEMORY_BARRIER();
    q->head = (q->head + 1) % QUEUE_CAPACITY;
    ATOMIC_DEC(q->count);
    return 0;
}

JAVIS_API int queue_size(JavisQueue* q) {
    return q ? q->count : 0;
}

JAVIS_API int queue_is_empty(JavisQueue* q) {
    return q ? (q->count == 0) : 1;
}

JAVIS_API int queue_is_full(JavisQueue* q) {
    return q ? (q->count >= QUEUE_CAPACITY) : 1;
}
