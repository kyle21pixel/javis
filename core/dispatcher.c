/*
 * J.A.V.I.S. Dispatcher - bridges the C message queue to the Python AI agent
 * Communicates via TCP socket on localhost:9000
 */

#include "queue.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #pragma comment(lib, "ws2_32.lib")
  typedef SOCKET sock_t;
  #define CLOSE_SOCK(s) closesocket(s)
  #define INIT_SOCKETS() do { WSADATA w; WSAStartup(MAKEWORD(2,2), &w); } while(0)
  #define CLEANUP_SOCKETS() WSACleanup()
#else
  #include <sys/socket.h>
  #include <arpa/inet.h>
  #include <unistd.h>
  typedef int sock_t;
  #define CLOSE_SOCK(s) close(s)
  #define INIT_SOCKETS()
  #define CLEANUP_SOCKETS()
#endif

#define DISPATCH_PORT  9000
#define DISPATCH_HOST  "127.0.0.1"
#define POLL_INTERVAL_MS 200

static JavisQueue* g_queue = NULL;
static volatile int g_running = 1;

/*
 * Serialise a JavisMessage to a compact JSON string.
 * Returns bytes written (excluding null terminator), or -1 on error.
 */
static int message_to_json(const JavisMessage* msg, char* out, size_t out_size) {
    return snprintf(out, out_size,
        "{\"channel\":\"%s\","
        "\"sender\":\"%s\","
        "\"subject\":\"%s\","
        "\"timestamp\":%lld,"
        "\"body\":\"%s\"}\n",
        msg->channel,
        msg->sender,
        msg->subject,
        (long long)msg->timestamp,
        msg->body
    );
}

/*
 * Attempts to connect to the Python agent socket server.
 * Returns socket fd on success, INVALID_SOCKET/-1 on failure.
 */
static sock_t connect_to_agent(void) {
    sock_t s = socket(AF_INET, SOCK_STREAM, 0);
#ifdef _WIN32
    if (s == INVALID_SOCKET) return INVALID_SOCKET;
#else
    if (s < 0) return -1;
#endif

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons(DISPATCH_PORT);
    inet_pton(AF_INET, DISPATCH_HOST, &addr.sin_addr);

    if (connect(s, (struct sockaddr*)&addr, sizeof(addr)) != 0) {
        CLOSE_SOCK(s);
        return (sock_t)-1;
    }
    return s;
}

/*
 * Main dispatch loop — runs forever, draining the queue and forwarding
 * messages to the Python agent over TCP.
 */
void dispatcher_run(JavisQueue* q) {
    g_queue = q;
    INIT_SOCKETS();
    printf("[JAVIS-Dispatcher] Starting on port %d...\n", DISPATCH_PORT);

    while (g_running) {
        if (queue_is_empty(g_queue)) {
#ifdef _WIN32
            Sleep(POLL_INTERVAL_MS);
#else
            usleep(POLL_INTERVAL_MS * 1000);
#endif
            continue;
        }

        JavisMessage msg;
        if (queue_pop(g_queue, &msg) != 0) continue;

        char json[MAX_MSG_LEN + 1024];
        int len = message_to_json(&msg, json, sizeof(json));
        if (len <= 0) continue;

        sock_t sock = connect_to_agent();
        if ((int)sock < 0) {
            fprintf(stderr, "[JAVIS-Dispatcher] Cannot reach agent, requeueing...\n");
            queue_push(g_queue, &msg); /* put it back */
#ifdef _WIN32
            Sleep(1000);
#else
            sleep(1);
#endif
            continue;
        }

        send(sock, json, len, 0);
        CLOSE_SOCK(sock);
        printf("[JAVIS-Dispatcher] Dispatched %s msg from %s\n", msg.channel, msg.sender);
    }

    CLEANUP_SOCKETS();
}

void dispatcher_stop(void) { g_running = 0; }

int main(void) {
    JavisQueue* q = queue_create();
    if (!q) { fprintf(stderr, "Failed to create queue\n"); return 1; }
    dispatcher_run(q);
    queue_destroy(q);
    return 0;
}
