# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import os

from fsspec import AbstractFileSystem


class WandbFileSystem(AbstractFileSystem):
    protocol = "wandb"

    def __init__(self, api_key: str = None) -> None:
        super().__init__()

        if api_key:
            os.environ["WANDB_API_KEY"] = api_key

        assert os.getenv("WANDB_API_KEY") is None, (
            "In order to connect to the wandb Public API you need to provide the"
            " API key either via param `api_key` or setting the key in the"
            " environment variable `WANDB_API_KEY`."
        )

        self.api = wandb.Api()
