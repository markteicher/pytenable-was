from unittest.mock import patch
from pytenable_was.http import HTTPClient
from pytenable_was.errors import TenableAPIError

def test_http_headers(http_client):
    headers = http_client._headers()
    assert "X-ApiKeys" in headers
    assert "AK" in headers["X-ApiKeys"]
    assert "SK" in headers["X-ApiKeys"]

@patch("requests.request")
def test_http_retry(mock_req, http_client):
    mock_req.return_value.status_code = 200
    mock_req.return_value.json.return_value = {"ok": True}

    resp = http_client.get("/test")
    assert resp == {"ok": True}

@patch("requests.request")
def test_http_error(mock_req, http_client):
    mock_req.return_value.status_code = 500
    mock_req.return_value.text = "ERR"

    try:
        http_client.get("/test")
        assert False, "Should not reach"
    except TenableAPIError:
        pass
