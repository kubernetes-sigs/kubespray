
SYSTEM=$(shell uname -s)

TARGETS+=lib/modules/custom_binary_producing_junk_$(SYSTEM)
TARGETS+=lib/modules/custom_binary_producing_json_$(SYSTEM)

all: clean $(TARGETS)

lib/modules/custom_binary_producing_junk_$(SYSTEM): lib/modules.src/custom_binary_producing_junk.c
	$(CC) -o $@ $<

lib/modules/custom_binary_producing_json_$(SYSTEM): lib/modules.src/custom_binary_producing_json.c
	$(CC) -o $@ $<

clean:
	rm -f $(TARGETS)
