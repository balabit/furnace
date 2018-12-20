#
# Copyright (c) 2016-2020 Balabit
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

import argparse
import pytest
from pathlib import Path

from furnace.cli import create_bind_mount_from_string
from furnace.config import BindMount


def test_create_bind_mount_from_sting():
    not_value_bind_mount_string = "/not/valid/volume/description"
    with pytest.raises(argparse.ArgumentTypeError):
        create_bind_mount_from_string(not_value_bind_mount_string)

    simple_bind_mount_string = "/home/test1:/home/test2"
    simple_bind_mount = BindMount(
        source=Path('/home/test1'),
        destination=Path('/home/test2'),
        readonly=True,
    )
    assert create_bind_mount_from_string(simple_bind_mount_string) == simple_bind_mount

    read_only_bind_mount_string = "/home/test3:/home/test4:ro"
    read_only_bind_mount = BindMount(
        source=Path('/home/test3'),
        destination=Path('/home/test4'),
        readonly=True,
    )
    assert create_bind_mount_from_string(read_only_bind_mount_string) == read_only_bind_mount

    read_write_bind_mount_string = "/home/test5:/home/test6:rw"
    read_write_bind_mount = BindMount(
        source=Path('/home/test5'),
        destination=Path('/home/test6'),
        readonly=False,
    )
    assert create_bind_mount_from_string(read_write_bind_mount_string) == read_write_bind_mount

    valid_bind_mount_string_with_not_valid_option = "/home/test7:/home/test8:not_valid_option"
    with pytest.raises(argparse.ArgumentTypeError):
        create_bind_mount_from_string(valid_bind_mount_string_with_not_valid_option)
