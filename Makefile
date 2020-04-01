#
# Copyright (c) 2013-2020 Balabit
#
# This file is part of Furnace.
#
# Furnace is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# Furnace is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Furnace.  If not, see <http://www.gnu.org/licenses/>.
#

.PHONY: autocs cs check check_copyright install dev clean doc

VIRTUALENV ?= .venv
PYCODESTYLE ?= $(VIRTUALENV)/bin/python3 -m pycodestyle
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
	$(PYCODESTYLE)

lint: dev
	$(FLAKE8)

check-copyright:
	test/check_copyright_headers.py

# Update requirements files for setup.py
update-requirements: $(VIRTUALENV)/bin/python3
	$(VIRTUALENV)/bin/pip3 install --upgrade pip-tools
	$(VIRTUALENV)/bin/pip-compile --no-emit-trusted-host --no-index --upgrade --output-file requirements-dev.txt requirements-dev.in

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

generate-badge:
	$(VIRTUALENV)/bin/anybadge --value='3.5 | 3.6 | 3.7 | 3.8' --label python --file python-support.svg --overwrite
