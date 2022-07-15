# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
from typing import List

import fsspec
import pytest

from wandbfsspec.core import WandbFile, WandbFileSystem


@pytest.mark.usefixtures("entity", "project", "run_id")
class TestFsspecFileSystem:
    """Test `fsspec.FileSystem` class methods for `wandbfs`."""

    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        self.fs = fsspec.filesystem(WandbFileSystem.protocol)
        self.path = (
            f"{WandbFileSystem.protocol}://{self.entity}/{self.project}/{self.run_id}"
        )

    def teardown(self):
        del self.fs

    def test_ls(self) -> None:
        """Test `fsspec.FileSystem.ls` method."""
        files = self.fs.ls(path=self.path)
        assert isinstance(files, List)

    def test_modified(self) -> None:
        """Test `fsspec.FileSystem.modified` method."""
        modified_at = self.fs.modified(path=f"{self.path}/file.yaml")
        assert isinstance(modified_at, datetime.datetime)

    def test_open(self) -> None:
        """Test `fsspec.FileSystem.open` method."""
        with self.fs.open(path=f"{self.path}/file.yaml") as f:
            assert isinstance(f, WandbFile)
