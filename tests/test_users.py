from pytenable_was.users import UsersAPI

def test_users_api_initialization(http_client):
    api = UsersAPI(http_client)
    assert hasattr(api, "fetch_all_users")
    assert hasattr(api, "enrich_scans")
