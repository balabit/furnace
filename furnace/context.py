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
from .libc import unshare, setns, CLONE_NEWPID

from .utils import PathEncoder

logger = logging.getLogger(__name__)


class ContainerPID1Manager:
    def __init__(self, root_dir: Path, *, isolate_networking=False):
        self.root_dir = root_dir.resolve()
        self.isolate_networking = isolate_networking

    def do_exec(self, control_read, control_write):
        logger.debug("Executing {} {}".format(sys.executable, pid1.__file__))
        params = json.dumps({
            "loglevel": logging.getLevelName(logger.getEffectiveLevel()),
            "root_dir": self.root_dir,
            "control_read": control_read,
            "control_write": control_write,
            "isolate_networking": self.isolate_networking,
        }, cls=PathEncoder)

        os.execl(sys.executable, sys.executable, pid1.__file__, params)

    def wait_for_ready_signal(self):
        if os.read(self.control_read, 3) != b"RDY":
            raise RuntimeError("Container PID 1 did not send Ready signal")

    def start(self):
        pipe_parent_read, pipe_child_write = os.pipe()
        pipe_child_read, pipe_parent_write = os.pipe()
        os.set_inheritable(pipe_child_read, True)
        os.set_inheritable(pipe_child_write, True)

        # We unshare (change) the pid namespace here, and other namespaces after
        # the exec, because if we exec'd in the new mount namespace, it would open
        # files in the new namespace's root, and prevent us from umounting the old
        # root after pivot_root. Note that changing the pid namespace affects only
        # the children (namely, which namespace they will be put in). It is thread
        # safe because unshare() affects the calling thread only.
        unshare(CLONE_NEWPID)

        self.pid = os.fork()
        if not self.pid:
            # this is the child process, will turn into PID1 in the container
            try:
                # this method will NOT return
                self.do_exec(pipe_child_read, pipe_child_write)
            except BaseException as e:
                # We are the child process, do NOT run parent's __exit__ handlers
                print(e, file=sys.stderr)
                os._exit(1)

        logger.debug("Container PID1 actual PID: {}".format(self.pid))

        # Reset the pid namespace of the parent process. /proc/self/ns/pid contains
        # a reference to the original pid namespace of the thread. New child processes
        # will be placed in this pid namespace after the setns() has restored the original
        # pid namespace
        original_pidns_fd = os.open('/proc/self/ns/pid', os.O_RDONLY)
        setns(original_pidns_fd, CLONE_NEWPID)
        os.close(original_pidns_fd)

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
    def __init__(self, root_dir: Path, *, isolate_networking=False):
        self.root_dir = root_dir.resolve()
        self.pid1 = ContainerPID1Manager(root_dir, isolate_networking=isolate_networking)

    def __enter__(self):
        self.pid1.start()
        return self

    def __exit__(self, type, value, traceback):
        self.pid1.kill()
        return False

    def assemble_nsenter_command(self, cmd):
        if not isinstance(cmd, list):
            raise TypeError("The cmd parameter must be an array")
        # The nsenter command is used instead of reimplementing its functionality in pure python.
        # because util-linux is a reasonable dependency, and actually entering PID namespaces are hard
        return ['nsenter', '-p', '-n', '-m', '-u', '-i', '-t', str(self.pid1.pid)] + cmd

    def run(self, cmd, shell=False, **kwargs):
        if shell:
            cmd = ['bash', '-c', cmd]
        return subprocess.run(self.assemble_nsenter_command(cmd), **kwargs)

    def interactive_shell(self, node):
        print()
        subprocess.run(
            self.assemble_nsenter_command(['bash', '--norc', '--noprofile', '-i']),
            env={
                'PS1': 'furnace-debug@{} \033[32m\w\033[0m # '.format(node)
            }
        )
