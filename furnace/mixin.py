#
# Copyright (c) 2006-2017 Balabit
# All Rights Reserved.
#

from .context import ContainerContext


class ContainerMixin:
    def __init__(self, *args, **kwargs):
        self.container = None

    def ensure_container_context(self, *, isolate_networking=False):
        self.container = ContainerContext(self.build_dir, isolate_networking=isolate_networking)
        return self.container
