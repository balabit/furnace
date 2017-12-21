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

from pathlib import Path

from .libc import CLONE_NEWPID, CLONE_NEWCGROUP, CLONE_NEWIPC, CLONE_NEWUTS, CLONE_NEWNS, CLONE_NEWNET, \
    MS_NOSUID, MS_NOEXEC, MS_NODEV, MS_RDONLY, MS_STRICTATIME

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
    {
        "destination": Path("/proc"),
        "type": "proc",
        "source": "proc"
    },
    {
        "destination": Path("/dev"),
        "type": "tmpfs",
        "source": "tmpfs",
        "flags": MS_NOSUID | MS_STRICTATIME,
        "options": [
            "mode=755",
            "size=65536k"
        ]
    },
    {
        "destination": Path("/dev/pts"),
        "type": "devpts",
        "source": "devpts",
        "flags": MS_NOSUID | MS_NOEXEC,
        "options": [
            "newinstance",
            "ptmxmode=0666",
            "mode=0620",
            "gid=5"
        ]
    },
    {
        "destination": Path("/dev/shm"),
        "type": "tmpfs",
        "source": "shm",
        "flags": MS_NOSUID | MS_NOEXEC | MS_NODEV,
        "options": [
            "mode=1777",
            "size=65536k"
        ]
    },
    {
        "destination": Path("/dev/mqueue"),
        "type": "mqueue",
        "source": "mqueue",
        "flags": MS_NOSUID | MS_NOEXEC | MS_NODEV,
    },
    {
        "destination": Path("/sys"),
        "type": "sysfs",
        "source": "sysfs",
        "flags": MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_RDONLY,
    },
    {
        "destination": Path("/run"),
        "type": "tmpfs",
        "source": "shm",
        "flags": MS_NOSUID | MS_NOEXEC | MS_NODEV,
        "options": [
            "mode=1777",
            "size=65536k"
        ]
    },
]

CONTAINER_DEVICE_NODES = [
    {
        "name": "null",
        "major": 1,
        "minor": 3,
    },
    {
        "name": "zero",
        "major": 1,
        "minor": 5,
    },
    {
        "name": "full",
        "major": 1,
        "minor": 7,
    },
    {
        "name": "tty",
        "major": 5,
        "minor": 0,
    },
    {
        "name": "random",
        "major": 1,
        "minor": 8,
    },
    {
        "name": "urandom",
        "major": 1,
        "minor": 9,
    },
]
