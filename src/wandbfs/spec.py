# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import os
from pathlib import Path
from typing import Any, Dict, List, Union

import wandb
from wandb.sdk.wandb_run import Run
from fsspec import AbstractFileSystem


class WandbFileSystem(AbstractFileSystem):
    protocol = "wandb"

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
        self._run = None

        self.entity = entity
        self.project = project
        self.run_id = run_id

    @property
    def run(self) -> Run:
        if self._run is None:
            self._run = self.api.run(f"{self.entity}/{self.project}/{self.run_id}")
        return self._run

    def ls(self, path: Union[str, Path] = Path("./")) -> List[Dict[str, Any]]:
        path = Path(path) if isinstance(path, str) else path
        files = []
        for _file in self.run.files():
            if path not in Path(_file.name).parents:
                continue
            files.append(_file.__dict__["_attrs"])
        return files
