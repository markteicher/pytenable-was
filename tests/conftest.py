import pytest
from pytenable_was.http import HTTPClient

@pytest.fixture
def http_client():
    """Provide a dummy HTTP client for testing."""
    return HTTPClient(access_key="AK", secret_key="SK", proxy=None, timeout=3)
