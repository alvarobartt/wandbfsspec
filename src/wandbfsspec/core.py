# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
import os
import tempfile
import urllib.request
import warnings
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple, Union

import wandb
from fsspec import AbstractFileSystem
from fsspec.spec import AbstractBufferedFile

MAX_PATH_LENGTH_WITHOUT_FILE_PATH = 3
MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH = 5


class WandbFileSystem(AbstractFileSystem):
    protocol = "wandbfs"

    def __init__(
        self,
        api_key: Union[str, None] = None,
    ) -> None:
        super().__init__()

        if api_key:
            os.environ["WANDB_API_KEY"] = api_key

        assert os.getenv("WANDB_API_KEY"), (
            "In order to connect to the wandb Public API you need to provide the API"
            " key either via param `api_key`, setting the key in the environment"
            " variable `WANDB_API_KEY`, or running `wandb login <WANDB_API_KEY>`."
        )

        self.api = wandb.Api()

    @classmethod
    def split_path(
        self, path: str
    ) -> Tuple[str, Union[str, None], Union[str, None], Union[str, None]]:
        path = self._strip_protocol(path=path)
        path = path.lstrip("/")
        if "/" not in path:
            return (path, None, None, None)
        path = path.split("/")
        if len(path) > MAX_PATH_LENGTH_WITHOUT_FILE_PATH:
            return (
                *path[:MAX_PATH_LENGTH_WITHOUT_FILE_PATH],
                "/".join(path[MAX_PATH_LENGTH_WITHOUT_FILE_PATH:]),
            )
        path += [None] * (MAX_PATH_LENGTH_WITHOUT_FILE_PATH - len(path))
        return (*path, None)

    def ls(self, path: str, detail: bool = False) -> Union[List[str], Dict[str, Any]]:
        entity, project, run_id, file_path = self.split_path(path=path)
        if entity and project and run_id:
            _files = self.api.run(f"{entity}/{project}/{run_id}").files()
            base_path = f"{entity}/{project}/{run_id}"
            return self.__ls_files(
                _files=_files,
                base_path=f"{base_path}/{file_path}" if file_path else base_path,
                file_path=file_path if file_path else Path("./"),
                detail=detail,
            )
        elif entity and project:
            _files = self.api.runs(f"{entity}/{project}")
            base_path = f"{entity}/{project}"
            return self.__ls_projects_or_runs(
                _files=_files, base_path=base_path, detail=detail
            )
        elif entity:
            _files = self.api.projects(entity=entity)
            base_path = entity
            return self.__ls_projects_or_runs(
                _files=_files, base_path=base_path, detail=detail
            )
        return []

    @staticmethod
    def __ls_files(
        _files: List[str],
        base_path: Union[str, Path],
        file_path: Union[str, Path] = Path("./"),
        detail: bool = False,
    ) -> Union[List[str], Dict[str, Any]]:
        file_path = Path(file_path) if isinstance(file_path, str) else file_path
        files = []
        for _file in _files:
            if file_path not in Path(_file.name).parents:
                continue
            filename = Path(_file.name.replace(f"{file_path.as_posix()}/", ""))
            if filename.is_dir() or len(filename.parents) > 1:
                filename = filename.parent
                if (
                    any(f["name"] == f"{base_path}/{filename.name}" for f in files)
                    if detail
                    else f"{base_path}/{filename.name}" in files
                ):
                    continue
                files.append(
                    {
                        "name": f"{base_path}/{filename.name}",
                        "type": "directory",
                        "size": 0,
                    }
                    if detail
                    else f"{base_path}/{filename.name}"
                )
                continue
            files.append(
                {
                    "name": f"{base_path}/{filename.name}",
                    "type": "file",
                    "size": _file.size,
                }
                if detail
                else f"{base_path}/{filename.name}"
            )
        return files

    @staticmethod
    def __ls_projects_or_runs(
        _files: List[str], detail: bool = False
    ) -> Union[List[str], Dict[str, Any]]:
        files = []
        for _file in _files:
            files.append(
                {
                    "name": _file.name,
                    "type": "directory",
                    "size": 0,
                }
                if detail
                else _file.name
            )
        return files

    def modified(self, path: str) -> datetime.datetime:
        """Return the modified timestamp of a file as a datetime.datetime"""
        entity, project, run_id, file_path = self.split_path(path=path)
        if not file_path:
            raise ValueError
        _file = self.api.run(f"{entity}/{project}/{run_id}").file(name=file_path)
        if not _file:
            raise ValueError
        return datetime.datetime.fromisoformat(_file.updated_at)

    def open(self, path: str, mode: Literal["rb", "wb"] = "rb") -> None:
        _, _, _, file_path = self.split_path(path=path)
        if not file_path:
            raise ValueError
        return WandbFile(self, path=path, mode=mode)

    def url(self, path: str) -> str:
        entity, project, run_id, file_path = self.split_path(path=path)
        _file = self.api.run(f"{entity}/{project}/{run_id}").file(name=file_path)
        if not _file:
            raise ValueError
        return _file.direct_url

    def cat_file(
        self, path: str, start: Union[int, None] = None, end: Union[int, None] = None
    ) -> bytes:
        url = self.url(path=path)
        req = urllib.request.Request(url=url)
        if not start and not end:
            start, end = 0, ""
        req.add_header("Range", f"bytes={start}-{end}")
        return urllib.request.urlopen(req).read()

    def put_file(self, lpath: str, rpath: str, **kwargs) -> None:
        entity, project, run_id, file_path = self.split_path(path=rpath)
        run = self.api.run(f"{entity}/{project}/{run_id}")
        warnings.warn(
            "`rpath` should be a directory path not a file path, as in order to use"
            " file paths we'll need to wait upon"
            " https://github.com/wandb/client/pull/3929 merge",
            RuntimeWarning,
        )
        run.upload_file(path=lpath, root=file_path if file_path else ".")

    def get_file(
        self, lpath: str, rpath: str, overwrite: bool = False, **kwargs
    ) -> None:
        entity, project, run_id, file_path = self.split_path(path=rpath)
        file = self.api.run(f"{entity}/{project}/{run_id}").file(name=file_path)
        file.download(root=lpath, replace=overwrite)

    def rm_file(self, path: str) -> None:
        entity, project, run_id, file_path = self.split_path(path=path)
        file = self.api.run(f"{entity}/{project}/{run_id}").file(name=file_path)
        file.delete()

    def cp_file(self, path1: str, path2: str, **kwargs) -> None:
        warnings.warn(
            "`path2` should be a directory path not a file path, as in order to use"
            " file paths we'll need to wait upon"
            " https://github.com/wandb/client/pull/3924 merge",
            RuntimeWarning,
        )
        # with tempfile.NamedTemporaryFile() as f: f.name
        with tempfile.TemporaryDirectory() as f:
            self.get_file(lpath=f, rpath=path1, overwrite=True)
            _, _, _, file_path = self.split_path(path=path1)
            self.put_file(lpath=f"{f}/{file_path}", rpath=path2)


class WandbFile(AbstractBufferedFile):
    def __init__(
        self, fs: WandbFileSystem, path: str, mode: Literal["rb", "wb"] = "rb"
    ) -> None:
        super().__init__(fs=fs, path=path, mode=mode)

    def _fetch_range(
        self, start: Union[int, None] = None, end: Union[int, None] = None
    ) -> bytes:
        return self.fs.cat_file(path=self.path, start=start, end=end)


class WandbArtifactStore(AbstractFileSystem):
    protocol = "wandbas"

    def __init__(
        self,
        api_key: Union[str, None] = None,
    ) -> None:
        super().__init__()

        if api_key:
            os.environ["WANDB_API_KEY"] = api_key

        assert os.getenv("WANDB_API_KEY"), (
            "In order to connect to the wandb Public API you need to provide the API"
            " key either via param `api_key`, setting the key in the environment"
            " variable `WANDB_API_KEY`, or running `wandb login <WANDB_API_KEY>`."
        )

        self.api = wandb.Api()

    @classmethod
    def split_path(
        self, path: str
    ) -> Tuple[str, Union[str, None], Union[str, None], Union[str, None]]:
        path = self._strip_protocol(path=path)
        path = path.lstrip("/")
        if "/" not in path:
            return (path, *[None] * MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH)
        path = path.split("/")
        if len(path) > MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH:
            return (
                *path[:MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH],
                "/".join(path[MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH:]),
            )
        path += [None] * (MAX_ARTIFACT_LENGTH_WITHOUT_FILE_PATH - len(path))
        return (*path, None)

    def ls(self, path: str, detail: bool = False) -> Union[List[str], Dict[str, Any]]:
        (
            entity,
            project,
            artifact_type,
            artifact_name,
            artifact_version,
            _,
        ) = self.split_path(path=path)
        if entity and project and artifact_type and artifact_name and artifact_version:
            return [
                f"{entity}/{project}/{artifact_type}/{artifact_name}/{artifact_version}/{f.name}"
                for f in self.api.artifact(
                    name=f"{entity}/{project}/{artifact_name}:{artifact_version}",
                    type=artifact_type,
                )._files()
            ]
        elif entity and project and artifact_type and artifact_name:
            return [
                f"{entity}/{project}/{artifact_type}/{artifact_name}/{v.name.split(':')[1]}"
                for v in self.api.artifact_versions(
                    name=f"{entity}/{project}/{artifact_name}", type_name=artifact_type
                )
            ]
        elif entity and project and artifact_type:
            return [
                f"{entity}/{project}/{artifact_type}/{c.name}"
                for c in self.api.artifact_type(
                    project=f"{entity}/{project}", type_name=artifact_type
                ).collections()
            ]
        elif entity and project:
            return [
                f"{entity}/{project}/{a.name}"
                for a in self.api.artifact_types(project=f"{entity}/{project}")
            ]
        elif entity:
            return [f"{entity}/{p.name}" for p in self.api.projects(entity=entity)]
        return []
