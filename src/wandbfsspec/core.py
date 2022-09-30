# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import os
import urllib.request
from typing import Any, Literal, Union

import wandb
from fsspec.spec import AbstractBufferedFile, AbstractFileSystem

__all__ = ["WandbFile", "WandbBaseFileSystem"]


class WandbFile(AbstractBufferedFile):  # type: ignore
    def __init__(
        self, fs: AbstractFileSystem, path: str, mode: Literal["rb", "wb"] = "rb"
    ) -> None:
        super().__init__(fs=fs, path=path, mode=mode)

    def _fetch_range(
        self, start: Union[int, None] = None, end: Union[int, None] = None
    ) -> Any:
        return self.fs.cat_file(path=self.path, start=start, end=end)


class WandbBaseFileSystem(AbstractFileSystem):  # type: ignore
    protocol: Literal["wandbfs", "wandbas"]

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
    def split_path(self, path: str) -> Any:
        raise NotImplementedError("Needs to be implemented!")

    def open(self, path: str, mode: Literal["rb", "wb"] = "rb") -> WandbFile:
        *_, file_path = self.split_path(path=path)
        if not file_path:
            raise ValueError
        return WandbFile(self, path=path, mode=mode)

    def url(self, path: str) -> str:
        raise NotImplementedError("Needs to be implemented!")

    def cat_file(
        self, path: str, start: Union[int, None] = None, end: Union[int, None] = None
    ) -> Any:
        url = self.url(path=path)
        req = urllib.request.Request(url=url)
        if not start and not end:
            start, end = 0, ""  # type: ignore
        req.add_header("Range", f"bytes={start}-{end}")
        return urllib.request.urlopen(req).read()
