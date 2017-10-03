#
# Copyright (c) 2006-2017 Balabit
# All Rights Reserved.
#

import json
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

from . import pid1
from .libc import clone, is_mount_point, CLONE_NEWPID

from bake.mount import BindMountContext
from bake.utils import hostrun, PathEncoder

logger = logging.getLogger(__name__)


class ContainerPID1Manager:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()

    def do_exec(self, control_read, control_write):
        logger.debug("Executing {} {}".format(sys.executable, pid1.__file__))
        params = json.dumps({
            "loglevel": logging.getLevelName(logger.getEffectiveLevel()),
            "root_dir": self.root_dir,
            "control_read": control_read,
            "control_write": control_write,
        }, cls=PathEncoder)

        os.execl(sys.executable, sys.executable, pid1.__file__, params)

    def wait_for_ready_signal(self):
        if os.read(self.control_read, 3) != b"RDY":
            raise RuntimeError("Container PID 1 did not send Ready signal")

    def start(self):
        if not is_mount_point(self.root_dir):
            # The pivot_root we call later only works with mountpoints
            raise ValueError("Container root must be a mountpoint.")
        pipe_parent_read, pipe_child_write = os.pipe()
        pipe_child_read, pipe_parent_write = os.pipe()
        os.set_inheritable(pipe_child_read, True)
        os.set_inheritable(pipe_child_write, True)

        # We will unshare the other namespaces after the exec,
        # because if we exec in the new mount namespace, it will open
        # files in the new namespace's root, and prevent us from umounting
        # the old root after pivot_root
        self.pid = clone(signal.SIGCHLD | CLONE_NEWPID)
        if not self.pid:
            try:
                # this method will NOT return
                self.do_exec(pipe_child_read, pipe_child_write)
            except BaseException as e:
                # We are the child process, do NOT run parent's __exit__ handlers
                print(e, file=sys.stderr)
                os._exit(1)
        logger.debug("Container PID1 actual PID: {}".format(self.pid))
        os.close(pipe_child_read)
        os.close(pipe_child_write)
        self.control_read = pipe_parent_read
        self.control_write = pipe_parent_write
        self.wait_for_ready_signal()

    def kill(self):
        # Killing pid1 will kill every other process in the context
        # The context itself will implode without any references,
        # basically cleaning up everything
        os.kill(self.pid, signal.SIGKILL)
        os.waitpid(self.pid, 0)


class ContainerContext:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()
        self.pid1 = ContainerPID1Manager(root_dir)
        self.bind_mount_ctx = None
        pass

    def __enter__(self):
        if not is_mount_point(self.root_dir):
            # Container root must be a mountpoint for pivot_root to work
            self.bind_mount_ctx = BindMountContext(self.root_dir, self.root_dir, remove_after_umount=False)
            self.bind_mount_ctx.__enter__()
        self.pid1.start()
        return self

    def __exit__(self, type, value, traceback):
        self.pid1.kill()
        if self.bind_mount_ctx:
            self.bind_mount_ctx.__exit__(type, value, traceback)
            self.bind_mount_ctx = None
        return False

    def assemble_nsenter_command(self, cmd):
        # The nsenter command is used instead of reimplementing its functionality in pure python.
        # because util-linux is a reasonable dependency, and actually entering PID namespaces are hard
        return ['nsenter', '-p', '-m', '-u', '-i', '-t', str(self.pid1.pid)] + cmd

    def run(self, cmd, shell=False, **kwargs):
        if shell:
            cmd = ['bash', '-c', cmd]
        return hostrun(self.assemble_nsenter_command(cmd), **kwargs)

    def interactive_shell(self):
        subprocess.Popen(self.assemble_nsenter_command(['bash', '-i'])).wait()
