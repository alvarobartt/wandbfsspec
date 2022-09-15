# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
from typing import List

import pytest

from wandbfsspec.core import WandbArtifactStore, WandbFile, WandbFileSystem


class TestWandbFileSystem:
    """Test `wandbfsspec.core.WandbFileSystem` class methods."""

    @pytest.fixture(autouse=True)
    @pytest.mark.usefixtures("entity", "project", "run_id")
    def setup_method(self, entity: str, project: str, run_id: str) -> None:
        self.fs = WandbFileSystem()
        self.path = f"{self.fs.protocol}://{entity}/{project}/{run_id}"

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


class TestWandbArtifactStore:
    """Test `wandbfsspec.core.WandbArtifactStore` class methods."""

    @pytest.fixture(autouse=True)
    @pytest.mark.usefixtures(
        "entity", "project", "artifact_type", "artifact_name", "artifact_version"
    )
    def setup_method(
        self,
        entity: str,
        project: str,
        artifact_type: str,
        artifact_name: str,
        artifact_version: str,
    ) -> None:
        self.fs = WandbArtifactStore()
        self.path = f"{self.fs.protocol}://{entity}/{project}/{artifact_type}/{artifact_name}/{artifact_version}"
        self.file_path = "file.yaml"

    def teardown(self):
        del self.fs

    def test_ls(self) -> None:
        """Test `WandbArtifactStore.ls` method."""
        files = self.fs.ls(path=self.path)
        assert isinstance(files, List)

    def test_created(self) -> None:
        created = self.fs.created(path=f"{self.path}/{self.file_path}")
        assert isinstance(created, datetime.datetime)

    def test_modified(self) -> None:
        modified_at = self.fs.modified(path=f"{self.path}/{self.file_path}")
        assert isinstance(modified_at, datetime.datetime)
