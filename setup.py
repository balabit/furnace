#!/usr/bin/env python3
# Copyright (c) 2016-2017 Balabit
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
import os
import sys
from setuptools import setup, find_packages
from furnace.version import get_version

if sys.version_info < (3, 5):
    sys.exit('Python version 3.5+ is required for furnace')

dev_requirements = [
    'autopep8==1.3.3',
    'flake8==3.5.0',
    'pep8==1.7.1',
    'pytest-cov==2.5.1',   # Note: do not sort the list: pytest-cov must be before pytest
    'pytest==3.2.3',
]

with open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='furnace',
    version=get_version(),
    description='A lightweight pure-python container implementation',
    long_description=long_description,
    url='https://github.com/balabit/furnace',
    keywords='containers containerization',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: System',
    ],
    packages=find_packages(include=["furnace*"]),
    extras_require={
        'dev': dev_requirements
    },
    package_data={'furnace': [
        'VERSION',
    ]},
    python_requires=">=3.5",
)
