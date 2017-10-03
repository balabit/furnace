#
# Copyright (c) 2006-2017 Balabit
# All Rights Reserved.
#
from pathlib import Path

from .libc import CLONE_NEWPID, CLONE_NEWCGROUP, CLONE_NEWIPC, CLONE_NEWUTS, CLONE_NEWNS, \
    MS_NOSUID, MS_NOEXEC, MS_NODEV, MS_RDONLY, MS_STRICTATIME

HOSTNAME = 'localhost'

NAMESPACES = {
    "pid": CLONE_NEWPID,
    "cgroup": CLONE_NEWCGROUP,
    "ipc": CLONE_NEWIPC,
    "uts": CLONE_NEWUTS,
    "mnt": CLONE_NEWNS,
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
