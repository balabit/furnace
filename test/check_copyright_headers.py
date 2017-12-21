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

import itertools
import os
import stat
import subprocess
import sys

COPYRIGHT_STRING = """This file is part of Furnace.

Furnace is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 2.1 of the License, or
(at your option) any later version.

Furnace is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Furnace.  If not, see <http://www.gnu.org/licenses/>."""

COPYRIGHT_MAX_LINES = 30

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
CHECK_EXTENSIONS = [
    'py',
]

INCLUDED_FILES = [
    'Makefile',
]


def log_error(msg):
    print(msg, file=sys.stderr)


def log_copyright_error(filename, msg, line=None):
    if line:
        msg = "{} (parsed line: '{}')".format(msg, line)
    log_error('{}: {}'.format(filename, msg))


def check_git_availability():
    result = subprocess.run(['git', 'rev-parse'])
    if result.returncode != 0:
        log_error('This script is intended to be run in checked-out git repositories to')
        log_error('determine the last change date of files and to exclude ignored ones')
        sys.exit(0)


def git_ls_files():
    ran = subprocess.run(
        ['git', 'ls-files', '--cached', '-o', '--exclude-standard'],
        stdout=subprocess.PIPE,
        cwd=PROJECT_ROOT
    )
    files = ran.stdout.decode().strip().split('\n')
    files = [os.path.join(PROJECT_ROOT, filename) for filename in files if os.path.isfile(os.path.join(PROJECT_ROOT, filename))]
    return files


def file_copyright_is_ok(filename):
    if os.stat(filename).st_size == 0:
        return True

    with open(filename) as f:
        head = list(itertools.islice(f, COPYRIGHT_MAX_LINES))

    index_in_copyright_text = 0
    copyright_lines = COPYRIGHT_STRING.split("\n")
    for head_line in head:
        if copyright_lines[index_in_copyright_text] in head_line:
            index_in_copyright_text = index_in_copyright_text + 1
        if index_in_copyright_text >= len(copyright_lines):
            break

    if index_in_copyright_text != len(copyright_lines):
        log_error("LGPL copyright string not found in {}".format(filename))
        return False
    return True


def is_executable_script(filename):
    if os.stat(filename).st_mode & stat.S_IXUSR:
        with open(filename, 'rb') as f:
            if f.read(2) == b'#!':
                return True

    return False


def has_specific_extension(filename):
    for ext in CHECK_EXTENSIONS:
        if filename.endswith('.' + ext):
            return True

    return False


def is_included_file(filename):
    for ext in INCLUDED_FILES:
        if os.path.basename(filename) == ext:
            return True

    return False


def is_everything_ok():
    everything_ok = True
    for filename in git_ls_files():
        check_file = is_executable_script(filename) or has_specific_extension(filename) or is_included_file(filename)
        if check_file and not file_copyright_is_ok(filename):
            everything_ok = False

    return everything_ok


if __name__ == "__main__":
    if not is_everything_ok():
        sys.exit(1)
