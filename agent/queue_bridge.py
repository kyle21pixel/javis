"""
J.A.V.I.S. Queue Bridge — Python ctypes wrapper around the compiled C queue DLL
Allows Python to push messages into the C ring buffer for the dispatcher.
"""
import ctypes
import os
import sys
import platform

# ── Load the compiled C shared library ───────────────────────────────────────

def _load_library():
    base = os.path.join(os.path.dirname(__file__), "..", "core")
    if platform.system() == "Windows":
        lib_path = os.path.join(base, "javis_queue.dll")
    else:
        lib_path = os.path.join(base, "javis_queue.so")

    lib_path = os.path.abspath(lib_path)
    if not os.path.exists(lib_path):
        print(f"[JAVIS-Queue] ⚠ C library not found at {lib_path}. Queue bridge disabled.")
        return None
    try:
        lib = ctypes.CDLL(lib_path)
        print(f"[JAVIS-Queue] ✅ Loaded C queue library: {lib_path}")
        return lib
    except Exception as e:
        print(f"[JAVIS-Queue] ⚠ Could not load C library: {e}")
        return None


# ── C struct mirror ───────────────────────────────────────────────────────────

class CJavisMessage(ctypes.Structure):
    _fields_ = [
        ("channel",   ctypes.c_char * 32),
        ("sender",    ctypes.c_char * 256),
        ("subject",   ctypes.c_char * 512),
        ("body",      ctypes.c_char * 4096),
        ("timestamp", ctypes.c_int64),
        ("processed", ctypes.c_int),
    ]


# ── Queue Bridge class ────────────────────────────────────────────────────────

class QueueBridge:
    def __init__(self):
        self._lib = _load_library()
        self._queue = None

        if self._lib:
            try:
                self._lib.queue_create.restype  = ctypes.c_void_p
                self._lib.queue_destroy.argtypes = [ctypes.c_void_p]
                self._lib.queue_push.argtypes    = [ctypes.c_void_p, ctypes.POINTER(CJavisMessage)]
                self._lib.queue_push.restype     = ctypes.c_int
                self._lib.queue_size.argtypes    = [ctypes.c_void_p]
                self._lib.queue_size.restype     = ctypes.c_int
                self._queue = self._lib.queue_create()
            except Exception as e:
                print(f"[JAVIS-Queue] Init error: {e}")
                self._lib = None

    def push(self, channel: str, sender: str, subject: str, body: str) -> bool:
        """Push a message into the C ring buffer."""
        if not self._lib or not self._queue:
            return False
        try:
            msg = CJavisMessage()
            msg.channel = channel.encode("utf-8")[:31]
            msg.sender  = sender.encode("utf-8")[:255]
            msg.subject = subject.encode("utf-8")[:511]
            msg.body    = body.encode("utf-8")[:4095]
            result = self._lib.queue_push(self._queue, ctypes.byref(msg))
            return result == 0
        except Exception as e:
            print(f"[JAVIS-Queue] Push error: {e}")
            return False

    def size(self) -> int:
        if not self._lib or not self._queue:
            return 0
        return self._lib.queue_size(self._queue)

    def is_available(self) -> bool:
        return self._lib is not None and self._queue is not None

    def __del__(self):
        if self._lib and self._queue:
            self._lib.queue_destroy(self._queue)


# Singleton instance
queue_bridge = QueueBridge()
