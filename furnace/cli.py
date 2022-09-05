#
# Copyright (c) 2016-2018 Balabit
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
import sys
import tempfile
from pathlib import Path

from . import version
from .config import BindMount
from .context import ContainerContext
from .utils import OverlayfsMountContext


DESCRIPTION = "A lightweight pure-python container implementation."


def parse_arguments(argv):
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        'root_dir',
        help="This directory will be the root directory of the container"
    )
    parser.add_argument(
        'cmd',
        nargs='*',
        help="the command that will be run. If empty, furnace will drop into an interactive shell"
    )
    parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s {version}'.format(version=version.get_version()),
    )
    parser.add_argument(
        '-H', '--hostname',
        default='container',
        help="virtual hostname setting for interactive shell"
    )
    parser.add_argument(
        '-i', '--isolate-networking',
        action='store_true',
        help="create an isolated networking namespace for the container"
    )
    parser.add_argument(
        '-p', '--persistent',
        action='store_true',
        help="do not create a temporary overlay on top of the root directory, the changes will be persistent"
    )
    parser.add_argument(
        '-v', '--volume',
        action='append',
        metavar='src:dst:{rw,ro}',
        default=[],
        type=create_bind_mount_from_string,
        dest='volumes',
        help="add volumes from the host machine to the container in the following format: "
        "/source/from/the/host:/path/in/the/container:rw, (readonly mount is the default)"
    )
    return parser.parse_args(argv[1:])


def create_bind_mount_from_string(volume):
    if ':' not in volume:
        raise argparse.ArgumentTypeError("Volume specification should have the following format: '/source/from/the/host:/path/in/the/container:rw'")

    source, destination = volume.split(':', 1)
    readonly = True
    if ':' in destination:
        destination, readwrite = destination.split(':', 1)
        if readwrite == 'ro':
            readonly = True
        elif readwrite == 'rw':
            readonly = False
        else:
            raise argparse.ArgumentTypeError('For creating volumes use the "ro", "rw" labels.')

    return BindMount(Path(source), Path(destination), readonly)


def run_container(root_dir, bind_mounts, isolate_networking, hostname, cmd):
    with ContainerContext(root_dir, isolate_networking=isolate_networking, bind_mounts=bind_mounts) as container:
        if cmd:
            container.run(cmd)
        else:
            container.interactive_shell(virtual_hostname=hostname)


def main(argv=sys.argv):
    args = parse_arguments(argv)
    if args.persistent:
        run_container(args.root_dir, args.volumes, args.isolate_networking, args.hostname, args.cmd)
    else:
        with tempfile.TemporaryDirectory(
            suffix="overlay_work"
        ) as overlay_workdir, tempfile.TemporaryDirectory(
            suffix="overlay_rw"
        ) as overlay_rwdir, tempfile.TemporaryDirectory(
            suffix="overlay_mount"
        ) as overlay_mounted, OverlayfsMountContext(
            [args.root_dir], overlay_rwdir, overlay_workdir, overlay_mounted
        ):
            run_container(overlay_mounted, args.volumes, args.isolate_networking, args.hostname, args.cmd)

    return 0


if __name__ == '__main__':
    sys.exit(main())
