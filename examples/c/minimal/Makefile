CC     =  gcc
CFLAGS =  --std=c99 -O2 -g -DNDEBUG
CFLAGS += -Wall -Wextra -Wpedantic -Wcast-align -Wcast-qual -Wformat=2 -Wmissing-include-dirs -Wnull-dereference -Woverloaded-virtual -Wpointer-arith -Wshadow -Wswitch-enum -Wvla -Wno-sign-compare -Wconversion -Wunused -Wold-style-cast -Wno-missing-braces
CFLAGS += -I ../../../dalaran_cpp/src/dalaran/c # Make sure dalaran.h is found
LDLIBS =

OBJECTS = main.o

ifeq ($(OS),Windows_NT)
	# TODO(emilk): Windows
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
		LDLIBS  += -lm
		OBJECTS += ../../../target/debug/libdalaran_c.a
    endif
    ifeq ($(UNAME_S),Darwin)
		# MacOS:
		LDLIBS  += -framework CoreFoundation -framework IOKit
		OBJECTS += ../../../target/debug/libdalaran_c.a
    endif
endif

all: example.bin

# Linking:
example.bin: dalaran_c $(OBJECTS)
	$(CC) $(CFLAGS) $(LDLIBS) $(OBJECTS) -o example.bin

# Compiling:
main.o: main.c
	$(CC) $(CFLAGS) -c main.c -o main.o

# Always rebuild dalaran_c; cargo will take care of not rebuilding unless needed
dalaran_c: FORCE
	cargo build -p dalaran_c

FORCE: ;

clean:
	rm -rf *.o *.bin

run: example.bin
	./example.bin
