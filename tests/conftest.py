import os
from pathlib import Path
os.environ['DATABASE_URL']='sqlite:///./test_reviver.db'
from api.database import Base, engine
import api.models
from fastapi.testclient import TestClient
from api.main import app
import pytest

@pytest.fixture(scope='session')
def client():
    with TestClient(app) as c:
        yield c
    engine.dispose()
    Base.metadata.drop_all(engine)
    Path('test_reviver.db').unlink(missing_ok=True)
