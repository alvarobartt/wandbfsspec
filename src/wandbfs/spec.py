# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import wandb
from fsspec import AbstractFileSystem

MAX_PATH_LENGTH_WITHOUT_FILEPATH = 3


class WandbFileSystem(AbstractFileSystem):
    protocol = "wandbfs"

    def __init__(
        self,
        api_key: Union[str, None] = None,
        entity: Union[str, None] = None,
        project: Union[str, None] = None,
        run_id: Union[str, None] = None,
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

    def ls(self, path: Union[str, Path] = Path("./")) -> List[Dict[str, Any]]:
        path = Path(path) if isinstance(path, str) else path
        files = []
        for _file in self.run.files():
            if path not in Path(_file.name).parents:
                continue
            files.append(_file.__dict__["_attrs"])
        return files
