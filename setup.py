#!/usr/bin/env python3
#
# Copyright (c) 2013-2017 Balabit
# All Rights Reserved.
#
import sys
from pathlib import Path

from setuptools import setup, find_packages
from setuptools.command.install import install

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

setup(
    name='furnace',
    version=get_version(),
    packages=find_packages(include=["furnace*"]),
    extras_require={
        'dev': dev_requirements
    },
    package_data={'bake': [
        'VERSION',
    ]},
    python_requires=">=3.5",
)
