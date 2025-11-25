import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import functools
from ..main import app
from .. import oauth2
from fastapi.testclient import TestClient
from datetime import datetime

class MockUser:
    def __init__(self, id, email, password, username):
        self.id = id
        self.email = email
        self.password = password
        self.username = username
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


mock_user = MockUser(id=347, email="test_super@test.com", password="test", username='Super Test')

def with_mocked_user(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        app.dependency_overrides[oauth2.get_current_user] = lambda: mock_user
        try:
            return func(*args, **kwargs)
        finally:
            del app.dependency_overrides[oauth2.get_current_user]
    return wrapper

client = TestClient(app)
