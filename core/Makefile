# J.A.V.I.S. Core — C Message Queue & Dispatcher
# Compiles on Windows (MinGW/GCC) and Linux/macOS

CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -std=c11

ifeq ($(OS),Windows_NT)
    DLL_NAME  = javis_queue.dll
    EXE_NAME  = javis_dispatcher.exe
    DLL_FLAGS = -shared -o $(DLL_NAME) -Wl,--out-implib,libjavis_queue.a
    LIBS      = -lws2_32
else
    DLL_NAME  = javis_queue.so
    EXE_NAME  = javis_dispatcher
    DLL_FLAGS = -shared -fPIC -o $(DLL_NAME)
    LIBS      =
endif

SRCS_LIB  = queue.c
SRCS_EXE  = dispatcher.c queue.c

.PHONY: all dll exe clean

all: dll exe

dll: $(SRCS_LIB)
	$(CC) $(CFLAGS) $(DLL_FLAGS) $(SRCS_LIB) $(LIBS)
	@echo "[JAVIS] Built shared library: $(DLL_NAME)"

exe: $(SRCS_EXE)
	$(CC) $(CFLAGS) -o $(EXE_NAME) $(SRCS_EXE) $(LIBS)
	@echo "[JAVIS] Built dispatcher: $(EXE_NAME)"

clean:
	del /Q *.dll *.exe *.a *.so 2>NUL || rm -f *.dll *.exe *.a *.so

