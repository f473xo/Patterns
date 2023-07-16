import pytest

from framework.api import API


@pytest.fixture
def api():
    return API()


@pytest.fixture
def client(api):
    return api.session()
