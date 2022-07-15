# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import os
from typing import Union

import wandb
from pydantic.dataclasses import dataclass

DATA_PATH = os.path.abspath("tests/data")
FILE_PATH = os.path.join(DATA_PATH, "file.yaml")
FILES_DIR = os.path.join(DATA_PATH, "files")


@dataclass
class MockRun:
    entity: str
    project: str
    run_name: Union[str, None] = None
    run_id: Union[str, None] = None

    def __post_init__(self):
        assert os.getenv("WANDB_API_KEY"), (
            "In order to connect to the wandb Public API you need to provide the API"
            " key either via param `api_key`, setting the key in the environment"
            " variable `WANDB_API_KEY`, or running `wandb login <WANDB_API_KEY>`."
        )

        assert wandb.run is None

        wandb.init(
            entity=self.entity, project=self.project, name=self.run_name, dir="/"
        )
        assert wandb.run is not None

        assert wandb.run._entity == self.entity
        assert wandb.run._project == self.project

        self.run_name = wandb.run._name
        self.run_id = wandb.run._run_id

        files = wandb.save(glob_str=FILE_PATH, policy="now")
        files = [os.path.relpath(file, wandb.run.dir) for file in files]
        assert os.path.basename(FILE_PATH) in files

        files = wandb.save(glob_str=f"{FILES_DIR}/*", base_path=DATA_PATH, policy="now")
        files = [os.path.relpath(file, f"{wandb.run.dir}/files") for file in files]
        assert all(file in files for file in os.listdir(FILES_DIR))

        wandb.finish()
        assert wandb.run is None
