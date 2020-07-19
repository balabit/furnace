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

import os
import pytest
import re
import subprocess
import threading
from pathlib import Path

from furnace.config import BindMount
from furnace.context import ContainerContext
from furnace.libc import is_mount_point
from furnace.utils import BindMountContext, OverlayfsMountContext


@pytest.fixture(scope="session")
def debootstrapped_dir(tmp_path_factory):
    result = os.environ.get("DEBOOTSTRAPPED_DIR")
    if not result:
        result = str(tmp_path_factory.mktemp('debootstrapped_dir'))
        subprocess.run(['debootstrap', 'xenial', result, 'http://archive.ubuntu.com/ubuntu'], check=True)
    yield Path(result)


@pytest.fixture
def rootfs_for_testing(debootstrapped_dir, tmp_path):
    overlay_workdir = tmp_path.joinpath('overlay_work')
    overlay_workdir.mkdir()
    overlay_rwdir = tmp_path.joinpath('overlay_rw')
    overlay_rwdir.mkdir()
    overlay_mounted = tmp_path.joinpath('overlay_mount')
    overlay_mounted.mkdir()
    with OverlayfsMountContext([debootstrapped_dir], overlay_rwdir, overlay_workdir, overlay_mounted):
        yield overlay_mounted


def test_container_basic(rootfs_for_testing):
    cwd = os.getcwd()
    with ContainerContext(rootfs_for_testing) as cnt:
        ps_output = cnt.run(['/bin/ps', '-e', '-o', 'pid,command', '--no-headers'], check=True, stdout=subprocess.PIPE).stdout
        ps_output = ps_output.decode('utf-8').split('\n')
        assert cwd == os.getcwd(), "Container.run() should not touch CWD"
        assert len(ps_output) > 0, 'There should be at least one process in the container (the ps). Might "ps" have failed?'
        assert len(ps_output) <= 3, \
            'There should be at most 3 processes in the container ' \
            '(init, ps, and possibly bash that runs ps).' \
            'Is it even contained? Is the proper /proc mounted?'

        false_output = cnt.run(['/bin/sh', '-c', 'exit 42'])
        assert false_output.returncode == 42, "Return codes of command should be preserved"

    assert cwd == os.getcwd(), "Container should not touch CWD"


def test_container_rootfs_is_not_mountpoint(debootstrapped_dir):
    assert not is_mount_point(debootstrapped_dir)
    with ContainerContext(debootstrapped_dir):
        pass


def test_container_rootfs_is_mountpoint(rootfs_for_testing):
    assert is_mount_point(rootfs_for_testing)
    with ContainerContext(rootfs_for_testing):
        pass


def test_mounts_visible_inside_container(rootfs_for_testing, tmp_path):
    with ContainerContext(rootfs_for_testing) as cnt:
        tmp_path.joinpath('test_file').write_text('Test data')
        mounted_after_path = rootfs_for_testing.joinpath('mounted_after')
        mounted_after_path.mkdir()
        with BindMountContext(tmp_path, mounted_after_path):
            output = cnt.run(['/bin/cat', '/mounted_after/test_file'], check=True, stdout=subprocess.PIPE).stdout
            assert output == b"Test data"


def test_files_made_in_container_visible_outside(rootfs_for_testing):
    with ContainerContext(rootfs_for_testing) as cnt:
        cnt.run(['/bin/dd', 'if=/dev/zero', 'of=/test_file', 'bs=128', 'count=1'], check=True)
        with rootfs_for_testing.joinpath('test_file').open('rb') as f:
            file_data = f.read()
        assert file_data == b'\0' * 128


def test_lingering_processes_are_killed(rootfs_for_testing):
    with ContainerContext(rootfs_for_testing) as cnt:
        cnt.run(['/bin/bash', '-c', '/bin/sleep 31337 >/dev/null 2>/dev/null&'], check=True)
        ps_output = subprocess.run(['/bin/ps', 'aux'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
        assert 'sleep 31337' in ps_output, 'The sleep should be running in the container'
    ps_output = subprocess.run(['/bin/ps', 'aux'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
    assert 'sleep 31337' not in ps_output, 'The sleep should no longer be running'


def test_zombies_are_killed(rootfs_for_testing):
    with ContainerContext(rootfs_for_testing) as cnt:
        # the || true is needed, otehrwise bash will exec the kill
        try:
            cnt.run(['/bin/bash', '-c', '/bin/bash -c "kill -9 $$ || true" || true'], check=True)
        except subprocess.CalledProcessError:
            pass
        ps_output = cnt.run(['/bin/ps', 'aux'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
        assert '<defunct>' not in ps_output, ''


def test_lock_dirs_are_present(rootfs_for_testing):
    with ContainerContext(rootfs_for_testing) as cnt:
        cnt.run(['/usr/bin/test', '-e', '/var/lock'], check=True)
        cnt.run(['/usr/bin/test', '-e', '/run/lock'], check=True)
        # no assert, because the previous two commands would have thrown an Exception on error


def test_networking_is_isolated_when_asked(rootfs_for_testing):
    with ContainerContext(rootfs_for_testing, isolate_networking=True) as cnt:
        ip_output = cnt.run(['/bin/ip', 'address', 'list'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
        assert re.search("^1: lo", ip_output, flags=re.MULTILINE) is not None, "Loopback interface should be present"
        assert re.search("^2: ", ip_output, flags=re.MULTILINE) is None, "No other interfaces should be present"


def test_networking_is_not_isolated_when_asked(rootfs_for_testing):
    with ContainerContext(rootfs_for_testing, isolate_networking=False) as cnt:
        ip_output = cnt.run(['/bin/ip', 'address', 'list'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
        assert re.search("^1: lo", ip_output, flags=re.MULTILINE) is not None, "Loopback interface should be present"
        assert re.search("^2: ", ip_output, flags=re.MULTILINE) is not None, "At least one other interface should be present"


def test_loop_mounts_work(rootfs_for_testing):
    with ContainerContext(rootfs_for_testing) as cnt:
        cnt.run(['/bin/dd', 'if=/dev/zero', 'of=/disk.img', 'bs=1M', 'count=10'], check=True)
        cnt.run(['/sbin/mkfs.ext4', '/disk.img'], check=True)
        rootfs_for_testing.joinpath('mounted').mkdir()
        cnt.run(['/bin/mount', '-o', 'loop', '/disk.img', '/mounted'], check=True)
        cnt.run(['/bin/touch', '/mounted/test.file'], check=True)
        # no assert, because the previous two commands would have thrown an Exception on error


def test_using_container_does_not_touch_files_if_network_isolated(debootstrapped_dir, tmp_path):
    overlay_workdir = tmp_path.joinpath('overlay_work')
    overlay_workdir.mkdir()
    overlay_rwdir = tmp_path.joinpath('overlay_rw')
    overlay_rwdir.mkdir()
    overlay_mounted = tmp_path.joinpath('overlay_mount')
    overlay_mounted.mkdir()
    with OverlayfsMountContext([debootstrapped_dir], overlay_rwdir, overlay_workdir, overlay_mounted):
        with ContainerContext(overlay_mounted, isolate_networking=True) as cnt:
            cnt.run(["/bin/ls", "/"], check=True)

    modified_files = list(overlay_rwdir.iterdir())
    assert len(modified_files) == 0, "No files should have been modified because of container run if network isolated"


def test_using_container_with_host_network(rootfs_for_testing, tmp_path):
    host_resolvconf_content = Path('/etc/resolv.conf').read_bytes()
    container_resolvconf_path = rootfs_for_testing.joinpath('etc', 'resolv.conf')
    if container_resolvconf_path.exists():
        container_resolvconf_path.unlink()
    with ContainerContext(rootfs_for_testing) as cnt:
        cnt.run(["/bin/ls", '-la', "/"], check=True)
        cnt.run(["/bin/mount"], check=True)

        touch_result = cnt.run(["/bin/touch", "/etc/resolv.conf"])
        assert touch_result.returncode != 0, "Touch should fail on resolv.conf, as it should be read-only"

        container_resolvconf_content = cnt.run(["/bin/cat", "/etc/resolv.conf"], check=True, stdout=subprocess.PIPE).stdout

    assert host_resolvconf_content == container_resolvconf_content, \
        "The content of '/etc/resolv.conf' of the host machine should be equal to '/etc/resolv.conf' of the container " \
        "if host networking is used"


class ThreadForTesting(threading.Thread):
    def __init__(self):
        super().__init__(name='container-test-ing-thread', daemon=True)
        self.stopme = False

    def run(self):
        # This thread is intentionally busy to test for
        # context-switch race conditions
        lcg = 1
        while self.stopme:
            lcg = (lcg * 1234567 + 1) % 87654321

    def stop(self):
        self.stopme = True
        self.join()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()


def test_thread_support(rootfs_for_testing):
    with ThreadForTesting():
        with ContainerContext(rootfs_for_testing) as cnt:
            cnt.run(['/bin/echo', 'Hello world'])
            cnt.Popen(['/bin/echo', 'Hello Popen']).wait()


def test_bind_mounts(rootfs_for_testing, tmp_path):
    tmp_path.joinpath('test_file').write_text('Test data')
    bind_mounts = [
        BindMount(tmp_path, Path('mounted', 'multiple', 'dirs'), False),
        BindMount(tmp_path, Path('mounted_ro'), True),
        BindMount(tmp_path.joinpath('test_file'), Path('mounted', 'as', 'file'), False),
        BindMount(tmp_path, Path('/', 'mounted', 'as', 'absolute'), False),
    ]

    with ContainerContext(rootfs_for_testing, bind_mounts=bind_mounts) as cnt:
        output = cnt.run(['/bin/cat', '/mounted/multiple/dirs/test_file'], check=True, stdout=subprocess.PIPE).stdout
        assert output == b"Test data"
        output = cnt.run(['/bin/cat', '/mounted_ro/test_file'], check=True, stdout=subprocess.PIPE).stdout
        assert output == b"Test data"
        output = cnt.run(['/bin/cat', '/mounted/as/file'], check=True, stdout=subprocess.PIPE).stdout
        assert output == b"Test data"
        output = cnt.run(['/bin/cat', '/mounted/as/absolute/test_file'], check=True, stdout=subprocess.PIPE).stdout
        assert output == b"Test data"
        result = cnt.run(['/bin/touch', '/mounted_ro/test_file'])
        assert result.returncode != 0, "Touch should fail, because mounted_ro should be read-only"

        assert not rootfs_for_testing.joinpath('mounted_ro', 'test_file').exists(), \
            "Bind mounts done by ContainerContext should not be visible outside of the container"


def test_ro_bind_mounts_from_outside(rootfs_for_testing, tmp_path):
    tmp_path.joinpath('test_file').write_text('Test data')

    mounted_before_path = rootfs_for_testing.joinpath('mounted_ro')
    mounted_before_path.mkdir()
    with BindMountContext(tmp_path, mounted_before_path, read_only=True):
        with pytest.raises(OSError):
            rootfs_for_testing.joinpath('mounted_ro', 'test_file').touch()
            pytest.fail("mounted_ro should be mounted readonly")
        with ContainerContext(rootfs_for_testing) as cnt:
            output = cnt.run(['/bin/cat', '/mounted_ro/test_file'], check=True, stdout=subprocess.PIPE).stdout
            assert output == b"Test data"
            result = cnt.run(['/bin/touch', '/mounted_ro/test_file'])
            assert result.returncode != 0, "Touch should fail, because mounted_ro should be read-only"
