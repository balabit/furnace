#
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

from collections import namedtuple

from pathlib import Path

from .libc import CLONE_NEWPID, CLONE_NEWCGROUP, CLONE_NEWIPC, CLONE_NEWUTS, CLONE_NEWNS, CLONE_NEWNET, \
    MS_NOSUID, MS_NOEXEC, MS_NODEV, MS_RDONLY, MS_STRICTATIME

Mount = namedtuple('Mount', ['destination', 'type', 'source', 'flags', 'options'])
DeviceNode = namedtuple('DeviceNode', ['name', 'major', 'minor'])
BindMount = namedtuple('BindMount', ['source', 'destination', 'readonly'])


HOSTNAME = 'localhost'

NAMESPACES = {
    "pid": CLONE_NEWPID,
    "cgroup": CLONE_NEWCGROUP,
    "ipc": CLONE_NEWIPC,
    "uts": CLONE_NEWUTS,
    "mnt": CLONE_NEWNS,
    "net": CLONE_NEWNET,
}

CONTAINER_MOUNTS = [
    Mount(
        destination=Path("/proc"),
        type="proc",
        source="proc",
        flags=0,
        options=None,
    ),
    Mount(
        destination=Path("/dev"),
        type="tmpfs",
        source="tmpfs",
        flags=MS_NOSUID | MS_STRICTATIME,
        options=[
            "mode=755",
            "size=65536k",
        ],
    ),
    Mount(
        destination=Path("/dev/pts"),
        type="devpts",
        source="devpts",
        flags=MS_NOSUID | MS_NOEXEC,
        options=[
            "newinstance",
            "ptmxmode=0666",
            "mode=0620",
            "gid=5",
        ],
    ),
    Mount(
        destination=Path("/dev/shm"),
        type="tmpfs",
        source="shm",
        flags=MS_NOSUID | MS_NOEXEC | MS_NODEV,
        options=[
            "mode=1777",
            "size=65536k",
        ],
    ),
    Mount(
        destination=Path("/dev/mqueue"),
        type="mqueue",
        source="mqueue",
        flags=MS_NOSUID | MS_NOEXEC | MS_NODEV,
        options=None,
    ),
    Mount(
        destination=Path("/sys"),
        type="sysfs",
        source="sysfs",
        flags=MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_RDONLY,
        options=None,
    ),
    Mount(
        destination=Path("/run"),
        type="tmpfs",
        source="shm",
        flags=MS_NOSUID | MS_NOEXEC | MS_NODEV,
        options=[
            "mode=1777",
            "size=65536k",
        ],
    ),
]

CONTAINER_DEVICE_NODES = [
    DeviceNode(
        name="null",
        major=1,
        minor=3,
    ),
    DeviceNode(
        name="zero",
        major=1,
        minor=5,
    ),
    DeviceNode(
        name="full",
        major=1,
        minor=7,
    ),
    DeviceNode(
        name="tty",
        major=5,
        minor=0,
    ),
    DeviceNode(
        name="random",
        major=1,
        minor=8,
    ),
    DeviceNode(
        name="urandom",
        major=1,
        minor=9,
    ),
]

HOST_NETWORK_BIND_MOUNTS = [
    BindMount(
        source=Path('/etc/resolv.conf'),          # path on host machine
        destination=Path('/etc/resolv.conf'),     # path in container
        readonly=True,
    ),
]
