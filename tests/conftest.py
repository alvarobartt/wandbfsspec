# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import os

import pytest

from .utils import MockRun

MOCK_RUN = MockRun(
    entity=os.getenv("WANDB_ENTITY", "alvarobartt"),
    project=os.getenv("WANDB_ENTITY", "wandbfsspec-tests"),
)


@pytest.fixture
def entity() -> str:
    return MOCK_RUN.entity


@pytest.fixture
def project() -> str:
    return MOCK_RUN.project


@pytest.fixture
def run_id() -> str:
    return MOCK_RUN.run_id
