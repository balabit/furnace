# Copyright (c) 2006-2017 Balabit
# All Rights Reserved

from pathlib import Path

version_file_path = Path(__file__).absolute().parent.joinpath('VERSION')

__version = None


def get_version():
    global __version

    if __version is None:
        with version_file_path.open('r') as version_file:
            __version = version_file.read().strip()

    return __version
