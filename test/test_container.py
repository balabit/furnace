#
# Copyright (c) 2006-2017 Balabit
# All Rights Reserved.
#

import os
import pytest
import subprocess
from bake.container.context import ContainerContext
from bake.container.libc import is_mount_point
from bake.builders.bootstrapbuilder import BootstrapBuilder
from bake.buildmanager import BuildManager
from bake.mount import BindMountContext
from bake.utils import hostrun


@pytest.fixture
def bootstrap(context):
    bm = BuildManager(context)
    builder = bm.build(BootstrapBuilder)
    yield builder


def test_container_basic(bootstrap):
    cwd = os.getcwd()
    with ContainerContext(bootstrap.build_dir) as cnt:
        ps_output = cnt.run(['ps', '-e', '-o', 'pid,command', '--no-headers'], need_output=True)
        ps_output = ps_output.decode('utf-8').split('\n')
        assert cwd == os.getcwd(), "Container.run() should not touch CWD"
        assert len(ps_output) > 0, 'There should be at least one process in the container (the ps). Might "ps" have failed?'
        assert len(ps_output) <= 3, \
            'There should be at most 3 processes in the container ' \
            '(init, ps, and possibly bash that runs ps).' \
            'Is it even contained? Is the proper /proc mounted?'

    assert cwd == os.getcwd(), "Container should not touch CWD"


def test_container_rootfs_is_not_mountpoint(bootstrap):
    assert not is_mount_point(bootstrap.build_dir)
    with ContainerContext(bootstrap.build_dir):
        pass


def test_container_rootfs_is_mountpoint(bootstrap):
    with BindMountContext(bootstrap.build_dir, bootstrap.build_dir, remove_after_umount=False):
        with ContainerContext(bootstrap.build_dir):
            pass


def test_mounts_visible_inside_container(bootstrap, tmpdir):
    with ContainerContext(bootstrap.build_dir) as cnt:
        with tmpdir.join("test_file").open("w") as f:
            f.write("Test data")

        with BindMountContext(str(tmpdir), os.path.join(bootstrap.build_dir, 'mounted_after')):
            output = cnt.run(['cat', '/mounted_after/test_file'], need_output=True)
            assert output == b"Test data"


def test_files_made_in_container_visible_outside(bootstrap, tmpdir):
    with ContainerContext(bootstrap.build_dir) as cnt:
        cnt.run(['dd', 'if=/dev/zero', 'of=/test_file', 'bs=128', 'count=1'])
        with open(os.path.join(bootstrap.build_dir, 'test_file'), 'rb') as f:
            file_data = f.read()
        assert file_data == b'\0' * 128


def test_lingering_processes_are_killed(bootstrap, tmpdir):
    with ContainerContext(bootstrap.build_dir) as cnt:
        cnt.run(['bash', '-c', 'sleep 31337 >/dev/null 2>/dev/null&'])
        ps_output = hostrun(['ps', 'aux'], need_output=True).decode('utf-8')
        assert 'sleep 31337' in ps_output, 'The sleep should be running in the container'
    ps_output = hostrun(['ps', 'aux'], need_output=True).decode('utf-8')
    assert 'sleep 31337' not in ps_output, 'The sleep should no longer be running'


def test_zombies_are_killed(bootstrap, tmpdir):
    with ContainerContext(bootstrap.build_dir) as cnt:
        # the || true is needed, otehrwise bash will exec the kill
        try:
            cnt.run(['bash', '-c', 'bash -c "kill -9 $$ || true" || true'])
        except subprocess.CalledProcessError:
            pass
        ps_output = cnt.run(['ps', 'aux'], need_output=True).decode('utf-8')
        assert '<defunct>' not in ps_output, ''
