# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
from typing import List

import fsspec
import pytest

from wandbfsspec.core import WandbFile


class TestFsspecFileSystem:
    """Test `fsspec.FileSystem` class methods for `wandbfs`."""

    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        self.fs = fsspec.filesystem("wandbfs")

    def teardown(self):
        del self.fs

    def test_ls(self) -> None:
        """Test `fsspec.FileSystem.ls` method."""
        files = self.fs.ls(path="wandbfs://alvarobartt/resnet-pytorch/3boz9td2/media")
        assert isinstance(files, List)

    def test_modified(self) -> None:
        """Test `fsspec.FileSystem.modified` method."""
        modified_at = self.fs.modified(
            path="wandbfs://alvarobartt/resnet-pytorch/3boz9td2/config.yaml"
        )
        assert isinstance(modified_at, datetime.datetime)

    def test_open(self) -> None:
        """Test `fsspec.FileSystem.open` method."""
        with self.fs.open(
            path="wandbfs://alvarobartt/resnet-pytorch/3boz9td2/config.yaml"
        ) as f:
            assert isinstance(f, WandbFile)
