# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
import os
import urllib.request
from pathlib import Path
from typing import List, Literal, Tuple, Union

import wandb
from fsspec import AbstractFileSystem
from fsspec.spec import AbstractBufferedFile

MAX_PATH_LENGTH_WITHOUT_FILEPATH = 3


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
        if len(path) > MAX_PATH_LENGTH_WITHOUT_FILEPATH:
            return (
                *path[:MAX_PATH_LENGTH_WITHOUT_FILEPATH],
                "/".join(path[MAX_PATH_LENGTH_WITHOUT_FILEPATH:]),
            )
        path += [None] * (MAX_PATH_LENGTH_WITHOUT_FILEPATH - len(path))
        return (*path, None)

    def ls(self, path: str, detail: bool = True) -> List[str]:
        entity, project, run_id, filepath = self.split_path(path=path)
        if entity and project and run_id:
            _files = self.api.run(f"{entity}/{project}/{run_id}").files()
        elif entity and project:
            _files = self.api.runs(f"{entity}/{project}")
        elif entity:
            _files = self.api.projects(entity=entity)
        else:
            return []
        filepath = Path(filepath if filepath else "./")
        files = []
        for _file in _files:
            filename = Path(_file.name)
            if filepath not in filename.parents:
                continue
            if not run_id or filename.is_dir():
                files.append(
                    {
                        "name": f"{entity}/{project}/{run_id}/{_file.name}",
                        "type": "directory",
                        "size": 0,
                    }
                    if detail
                    else f"{entity}/{project}/{run_id}/{_file.name}"
                )
                continue
            files.append(
                {
                    "name": f"{entity}/{project}/{run_id}/{_file.name}",
                    "type": "file",
                    "size": _file.size,
                }
                if detail
                else f"{entity}/{project}/{run_id}/{_file.name}"
            )
        return files

    def modified(self, path: str) -> datetime.datetime:
        """Return the modified timestamp of a file as a datetime.datetime"""
        entity, project, run_id, filepath = self.split_path(path=path)
        if not filepath:
            raise ValueError
        _file = self.api.run(f"{entity}/{project}/{run_id}").file(name=filepath)
        if not _file:
            raise ValueError
        return datetime.datetime.fromisoformat(_file.__dict__["_attrs"]["updatedAt"])

    def open(self, path: str, mode: Literal["rb", "wb"] = "rb") -> None:
        _, _, _, filepath = self.split_path(path=path)
        if not filepath:
            raise ValueError
        return WandbFile(self, path=path, mode=mode)

    def url(self, path: str) -> str:
        entity, project, run_id, filepath = self.split_path(path=path)
        _file = self.api.run(f"{entity}/{project}/{run_id}").file(name=filepath)
        if not _file:
            raise ValueError
        return _file._attrs["directUrl"]

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
        entity, project, run_id, filepath = self.split_path(path=rpath)
        run = self.api.run(f"{entity}/{project}/{run_id}")
        run.upload_file(path=lpath, root=Path(filepath).parents[0].as_posix())

    def get_file(self, lpath: str, rpath: str, overwrite: bool = False, **kwargs) -> None:
        entity, project, run_id, filepath = self.split_path(path=rpath)
        file = self.api.run(f"{entity}/{project}/{run_id}").file(name=filepath)
        file.download(root=lpath, replace=overwrite)


class WandbFile(AbstractBufferedFile):
    def __init__(
        self, fs: WandbFileSystem, path: str, mode: Literal["rb", "wb"] = "rb"
    ) -> None:
        super().__init__(fs=fs, path=path, mode=mode)

    def _fetch_range(
        self, start: Union[int, None] = None, end: Union[int, None] = None
    ) -> bytes:
        return self.fs.cat_file(path=self.path, start=start, end=end)
