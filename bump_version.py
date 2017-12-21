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

from pathlib import Path

version_file_path = Path(__file__).absolute().parent.joinpath('furnace', 'VERSION')


def main():
    with version_file_path.open('r') as version_file:
        current_version = version_file.read().strip()

    version_parts = [int(part) for part in current_version.split('.')]
    version_parts[-1] += 1
    bumped_version = '.'.join([str(part) for part in version_parts])

    with version_file_path.open('w') as version_file:
        version_file.write(bumped_version + '\n')

    print(bumped_version)


if __name__ == '__main__':
    main()
