# Copyright 2022 Alvaro Bartolome, alvarobartt @ GitHub
# See LICENSE for details.

import pytest


@pytest.fixture
def entity() -> str:
    return "alvarobartt"


@pytest.fixture
def project() -> str:
    return "resnet-pytorch"


@pytest.fixture
def run_id() -> str:
    return "3boz9td2"
