import os
from pathlib import Path
from tempfile import TemporaryDirectory

test_directory = TemporaryDirectory()
test_database = (Path(test_directory.name) / 'reviver.db').as_posix()
os.environ['DATABASE_URL'] = f'sqlite:///{test_database}'
from api.database import engine
import api.models
from fastapi.testclient import TestClient
from api.main import app
import pytest

@pytest.fixture(scope='session')
def client():
    with TestClient(app) as c:
        yield c
    engine.dispose()
    test_directory.cleanup()
