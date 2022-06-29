# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

from typing import List

import pytest

from wandbfs.spec import WandbFileSystem


class TestWandbFileSystem:
    """Test `wandbfs.spec.WandbFileSystem` class methods."""

    @pytest.fixture(autouse=True)
    @pytest.mark.usefixtures("entity", "project", "run_id")
    def setup_method(self, entity: str, project: str, run_id: str) -> None:
        self.fs = WandbFileSystem(entity=entity, project=project, run_id=run_id)

    def teardown(self):
        del self.fs

    def test_ls(self) -> None:
        """Test `WandbFileSystem.ls` method."""
        files = self.fs.ls(path="wandbfs://alvarobartt/resnet-pytorch")
        assert isinstance(files, List)
