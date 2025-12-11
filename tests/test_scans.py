from pytenable_was.scans import ScansAPI

def test_scans_api_initialization(http_client):
    api = ScansAPI(http_client)
    assert hasattr(api, "list_scans")
    assert hasattr(api, "change_owner_all")
