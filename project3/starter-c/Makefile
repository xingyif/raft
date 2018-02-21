SEND = 3700send
RECV = 3700recv
SENDRECV = 3700sendrecv

all: $(SEND) $(RECV)

$(SENDRECV).o: $(SENDRECV).c
	gcc -c -std=c99 -O0 -g -lm -Wall -pedantic -Wextra -o $@ $<

$(SEND): $(SEND).c $(SENDRECV).o
	gcc -std=c99 -O0 -g -lm -Wall -pedantic -Wextra -o $@ $< $(SENDRECV).o

$(RECV): $(RECV).c $(SENDRECV).o
	gcc -std=c99 -O0 -g -lm -Wall -pedantic -Wextra -o $@ $< $(SENDRECV).o

test: all
	./test

clean:
	rm $(SEND) $(RECV) $(SENDRECV).o

