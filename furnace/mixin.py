#
# Copyright (c) 2006-2017 Balabit
# All Rights Reserved.
#

from .context import ContainerContext


class ContainerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container = None

    def ensure_container_context(self):
        self.container = ContainerContext(self.build_dir)
        return self.container
