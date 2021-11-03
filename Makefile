
# \ var
MODULE      = $(notdir $(CURDIR))
OS          = $(shell uname -s)
CORES       = $(shell grep processor /proc/cpuinfo | wc -l)
# / var

# \ dir
CWD         = $(CURDIR)
BIN         = $(CWD)/bin
DOC         = $(CWD)/doc
LIB         = $(CWD)/lib
SRC         = $(CWD)/src
TMP         = $(CWD)/tmp
# / dir

# \ tool
CURL = curl -L -o
PY   = $(shell which python3)
PYT  = $(shell which pytest)
PEP  = $(shell which autopep8)
# / tool

# \ package
SYSLINUX_VER = 6.0.3
# / package

# \ src
Y += $(MODULE).py test_$(MODULE).py
P += config.py
S += $(Y)
# / src

# \ cfg
PEPS = E26,E302,E305,E401,E402,E701,E702
# / cfg

# \ all
.PHONY: meta
meta: $(Y)
	$(MAKE) test
	$(PY)   $(MODULE).py
	$(PEP)  --ignore=$(PEPS) --in-place $?

.PHONY: test
test: $(Y)
	$(PYT) test_$(MODULE).py
# / all


# \ doc
.PHONY: doc
doc: doc/pyMorphic.pdf
doc/pyMorphic.pdf:
	$(CURL) $@ http://www.diva-portal.org/smash/get/diva2:22296/FULLTEXT01.pdf
# / doc

# \ install
.PHONY: install update
install: $(OS)_install doc
	$(MAKE) test
update: $(OS)_update doc
	$(MAKE) test
.PHONY: Linux_install Linux_update
Linux_install Linux_update:
	sudo apt update
	sudo apt install -u `cat apt.txt`
# / install

# \ merge
SHADOW ?= ponymuck
MERGE   = Makefile .gitignore README.md apt.txt $(S)
MERGE  += .vscode bin doc lib src tmp

.PHONY: dev
dev:
	git push -v
	git checkout $@
	git checkout $(SHADOW) -- $(MERGE)

.PHONY: shadow
shadow:
	git push -v
	git checkout $(SHADOW)

.PHONY: release
release:

.PHONY: zip
zip:
# / merge
