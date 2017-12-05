#
# Copyright (c) 2013-2017 Balabit
# All Rights Reserved.
#

.PHONY: autocs cs check check_copyright install dev clean doc

VIRTUALENV ?= .venv
PEP8 ?= $(VIRTUALENV)/bin/python3 -m pep8
AUTOPEP8 ?= $(VIRTUALENV)/bin/python3 -m autopep8
FLAKE8 ?= $(VIRTUALENV)/bin/python3 -m flake8


# Auto format by coding style check
autocs: dev
	$(AUTOPEP8) --in-place --recursive .

# Auto format diff by coding style check
autocs-diff: dev
	$(AUTOPEP8) --diff --recursive .

# Coding style check
cs: dev
	$(PEP8)

lint: dev
	$(FLAKE8)

check-copyright:
	test/check_copyright_headers.py

# Run tests
check: check-copyright dev
	sudo PYTHONDONTWRITEBYTECODE=1 $(VIRTUALENV)/bin/pytest

# Create a virtualenv in .venv or the directory given in the following form: 'make VIRTUALENV=.venv2 install'
$(VIRTUALENV)/bin/python3:
	python3 -m venv $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip install --upgrade pip

# Install development dependencies (for testing) in virtualenv
dev: $(VIRTUALENV)/bin/python3
	$(VIRTUALENV)/bin/pip3 install --editable '.[dev]'

# Clean directory and delete virtualenv
clean:
	$(VIRTUALENV)/bin/python3 setup.py clean --all
	rm -rf $(VIRTUALENV)

get-version:
	cat furnace/VERSION

bump-version:
	./bump_version.py
