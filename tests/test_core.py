# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
from typing import List

import pytest

from wandbfsspec.core import WandbFile, WandbFileSystem


@pytest.mark.usefixtures("entity", "project", "run_id")
class TestWandbFileSystem:
    """Test `wandbfsspec.core.WandbFileSystem` class methods."""

    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        self.fs = WandbFileSystem()
        self.path = f"{self.fs.protocol}://{self.entity}/{self.project}/{self.run_id}"

    def teardown(self):
        del self.fs

    def test_ls(self) -> None:
        """Test `WandbFileSystem.ls` method."""
        files = self.fs.ls(path=self.path)
        assert isinstance(files, List)

    def test_modified(self) -> None:
        modified_at = self.fs.modified(path=f"{self.path}/file.yaml")
        assert isinstance(modified_at, datetime.datetime)

    def test_open(self) -> None:
        _file = self.fs.open(path=f"{self.path}/file.yaml")
        assert isinstance(_file, WandbFile)
