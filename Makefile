# \ var
MODULE = $(notdir $(CURDIR))
# / var

# \ tool
CURL = curl -L -o
PY   = $(shell which python3)
PEP  = $(shell which autopep8)
PEPS = E26,E302,E305,E401,E402,E701,E702
# / tool

# \ src
SRC = $(MODULE).py
# / src

# \ all
repl: $(SRC)
	$(PY) -i $<
	$(PEP) --ignore=$(PEPS) --in-place $?
	$(MAKE) $@
# / all

# \ doc

.PHONY: doc
doc: doc/diva2.pdf
doc/diva2.pdf:
	$(CURL) $@ http://www.diva-portal.org/smash/get/diva2:22296/FULLTEXT01.pdf
# / doc
