# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

from typing import List

import pytest

import datetime

from wandbfs.core import WandbFileSystem


class TestWandbFileSystem:
    """Test `wandbfs.core.WandbFileSystem` class methods."""

    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        self.fs = WandbFileSystem()

    def teardown(self):
        del self.fs

    def test_ls(self) -> None:
        """Test `WandbFileSystem.ls` method."""
        files = self.fs.ls(path="wandbfs://alvarobartt/resnet-pytorch")
        assert isinstance(files, List)

    def test_modified(self) -> None:
        modified_at = self.fs.modified(path="wandbfs://alvarobartt/resnet-pytorch/3boz9td2/config.yaml")
        assert isinstance(modified_at, datetime.datetime)

    def test_open(self) -> None:
        _file = self.fs.open(path="wandbfs://alvarobartt/resnet-pytorch/3boz9td2/config.yaml")
        assert isinstance(_file, bytes)

    def test_ls_from_fsspec(self) -> None:
        import fsspec
        fs = fsspec.filesystem("wandbfs")
        files = fs.ls(path="wandbfs://alvarobartt/resnet-pytorch")
        print(files)
        assert isinstance(files, List)

    def test_open_from_fsspec(self) -> None:
        import fsspec
        fs = fsspec.filesystem("wandbfs")
        with fs.open(path="wandbfs://alvarobartt/resnet-pytorch/3boz9td2/config.yaml", mode="rb") as f:
            print(f.read())
