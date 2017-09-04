#
# Copyright (c) 2006-2017 Balabit
# All Rights Reserved.
#

import json
import logging
import os
import signal
import stat
import sys

from bake.container.libc import unshare, mount, umount, non_caching_getpid, get_all_mounts, pivot_root, \
    MS_REC, MS_SLAVE, CLONE_NEWPID
from bake.container.config import NAMESPACES, CONTAINER_MOUNTS, CONTAINER_DEVICE_NODES
from bake.logger import setup_logging

logger = logging.getLogger("container.pid1")


class PID1:
    def __init__(self, root_dir, control_read, control_write):
        self.control_read = control_read
        self.control_write = control_write
        self.root_dir = os.path.abspath(root_dir)

    def enable_zombie_reaping(self):
        # We are pid 1, so we have to take care of orphaned processes
        # Interestingly, SIG_IGN is the default handler for SIGCHLD,
        # but this way we signal to the kernel that we will not call waitpid
        # and get rid of zombies automatically
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        pass

    def setup_root_mount(self):
        # SLAVE means that mount events will get inside the container, but
        # mounting something inside will not leak out.
        # Use PRIVATE to not let outside events propagate in
        mount("none", "/", None, MS_REC | MS_SLAVE, None)
        old_root_dir = os.path.join(self.root_dir, 'old_root')
        os.makedirs(old_root_dir, exist_ok=True)
        os.chdir(self.root_dir)
        pivot_root('.', 'old_root')
        os.chroot('.')

    def mount_defaults(self):
        for m in CONTAINER_MOUNTS:
            options = None
            if "options" in m:
                options = ",".join(m["options"])
            os.makedirs(m["destination"], exist_ok=True)
            mount(m["source"], m["destination"], m["type"], m.get("flags", 0), options)

    def create_default_dev_nodes(self):
        for d in CONTAINER_DEVICE_NODES:
            os.mknod(os.path.join("/dev", d["name"]), mode=stat.S_IFCHR, device=os.makedev(d["major"], d["minor"]))
            # A separate chmod is necessary, because mknod (undocumentedly) takes umask into account when creating
            os.chmod(os.path.join("/dev", d["name"]), 0o666)

    def umount_old_root(self):
        mounts = [m for m in get_all_mounts() if m.startswith('/old_root')]
        mounts.sort(key=len, reverse=True)
        for m in mounts:
            umount(m)
        os.rmdir('/old_root')

    def create_namespaces(self):
        unshare_flags = 0
        for flag in NAMESPACES.values():
            if flag != CLONE_NEWPID:
                unshare_flags = unshare_flags | flag
        unshare(unshare_flags)

    def run(self):
        if non_caching_getpid() != 1:
            raise ValueError("We are not actually PID1, exiting for safety reasons")

        # codecs are loaded dynamically, and won't work when we remount root
        make_sure_codecs_are_loaded = b'a'.decode('unicode_escape')
        os.setsid()
        self.enable_zombie_reaping()
        self.create_namespaces()
        self.setup_root_mount()
        self.mount_defaults()
        self.create_default_dev_nodes()
        self.umount_old_root()

        os.write(self.control_write, b"RDY")
        logger.debug("Container started")
        # this will return when the pipe is closed
        # E.g. the outside control process died before killing us
        os.read(self.control_read, 1)
        logger.debug("Control pipe closed, stopping")
        return 0


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    setup_logging(args['loglevel'])
    pid1 = PID1(args['root_dir'], args['control_read'], args['control_write'])
    sys.exit(pid1.run())
