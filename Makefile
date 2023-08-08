# To use this Makefile, get a copy of my SF Release Tools
# git clone git://git.code.sf.net/p/sfreleasetools/code sfreleasetools
# And point the environment variable RELEASETOOLS to the checkout
ifeq (,${RELEASETOOLS})
    RELEASETOOLS=../releasetools
endif
LASTRELEASE:=$(shell $(RELEASETOOLS)/lastrelease -n -rv)
VERSIONPY=filter_optimizer/Version.py
VERSION=$(VERSIONPY)
README=README.rst
PROJECT=filter-optimizer

all: $(VERSION)

clean:
	rm -f README.html filter_optimizer/Version.py
	rm -rf ${CLEAN} filter-optimizer.egg-info

.PHONY: clean test

include $(RELEASETOOLS)/Makefile-pyrelease
