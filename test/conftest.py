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

import pytest
import sys

from pathlib import Path


# NOTE: In Python versions before 3.6, pytest uses pathlib2
# instead of pathlib, which are not compatible with each other.
if sys.version_info < (3, 6):
    @pytest.fixture
    def tmp_path(tmp_path):
        yield Path(str(tmp_path))
