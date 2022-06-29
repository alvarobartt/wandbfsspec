# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import datetime
import os
from pathlib import Path
from typing import List, Tuple, Union

import wandb
from fsspec import AbstractFileSystem

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

        assert os.getenv("WANDB_API_KEY") is None, (
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
        if not entity:
            return []
        if entity and not project and not run_id:
            _files = self.api.projects(entity=entity)
        if entity and project and not run_id:
            _files = self.api.runs(f"{entity}/{project}")
        if entity and project and run_id:
            _files = self.api.run(f"{entity}/{project}/{run_id}").files()
        filepath = Path(filepath if filepath else "./")
        files = []
        for _file in _files:
            if filepath not in Path(_file.name).parents:
                continue
            files.append(
                {
                    "name": f"{entity}/{project}/{run_id}/{_file.name}",
                    "size": _file.size,
                }
            )
        return files if detail else [f["name"] for f in files]

    def modified(self, path: str) -> datetime.datetime:
        """Return the modified timestamp of a file as a datetime.datetime"""
        entity, project, run_id, filepath = self.split_path(path=path)
        if not filepath:
            raise ValueError
        _file = self.api.run(f"{entity}/{project}/{run_id}").file(name=filepath)
        if not _file:
            raise ValueError
        return datetime.datetime.fromisoformat(_file.__dict__["_attrs"]["updatedAt"])
