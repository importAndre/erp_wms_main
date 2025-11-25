import random
from .mock_user import client, with_mocked_user

def test_create_user():
    n = random.randint(0, 1000)