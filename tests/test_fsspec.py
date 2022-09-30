# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
from typing import List

import fsspec
import pytest

from wandbfsspec.core import WandbFile


class TestFsspecFileSystem:
    """Test `fsspec.FileSystem` class methods for `wandbfs` and `wandbas`."""

    @pytest.fixture(autouse=True)
    @pytest.mark.usefixtures(
        "protocol",
        "entity",
        "project",
        "run_id",
        "artifact_type",
        "artifact_name",
        "artifact_version",
    )
    def setup_method(
        self,
        protocol: str,
        entity: str,
        project: str,
        run_id: str,
        artifact_type: str,
        artifact_name: str,
        artifact_version: str,
    ) -> None:
        self.fs = fsspec.filesystem(protocol)

        self.base_path = f"{protocol}://{entity}/{project}"
        self.path = (
            f"{self.base_path}/{run_id}"
            if protocol == "wandbfs"
            else f"{self.base_path}/{artifact_type}/{artifact_name}/{artifact_version}"
        )
        self.file_path = "file.yaml"

    def teardown(self) -> None:
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
