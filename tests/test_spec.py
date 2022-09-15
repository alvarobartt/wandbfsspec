# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
from typing import List

import fsspec
import pytest

from wandbfsspec.core import WandbFile, WandbFileSystem


class TestFsspecFileSystem:
    """Test `fsspec.FileSystem` class methods for `wandbfs`."""

    @pytest.fixture(autouse=True)
    @pytest.mark.usefixtures("entity", "project", "run_id")
    def setup_method(self, entity: str, project: str, run_id: str) -> None:
        self.fs = fsspec.filesystem(WandbFileSystem.protocol)
        self.path = f"{WandbFileSystem.protocol}://{entity}/{project}/{run_id}"
        self.file_path = "file.yaml"

    def teardown(self):
        del self.fs

    def test_ls(self) -> None:
        """Test `fsspec.FileSystem.ls` method."""
        files = self.fs.ls(path=self.path)
        assert isinstance(files, List)

    def test_modified(self) -> None:
        """Test `fsspec.FileSystem.modified` method."""
        modified_at = self.fs.modified(path=f"{self.path}/{self.file_path}")
        assert isinstance(modified_at, datetime.datetime)

    def test_open(self) -> None:
        """Test `fsspec.FileSystem.open` method."""
        with self.fs.open(path=f"{self.path}/{self.file_path}") as f:
            assert isinstance(f, WandbFile)
