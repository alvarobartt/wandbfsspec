# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import os

import wandb
from fsspec import AbstractFileSystem


class WandbFileSystem(AbstractFileSystem):
    protocol = "wandb"

    def __init__(
        self,
        api_key: str = None,
        entity: str = None,
        project: str = None,
        run_id: str = None,
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
    def run(self):
        if self._run is None:
            self._run = self.api.run(f"{self.entity}/{self.project}/{self.run_id}")
        return self._run
