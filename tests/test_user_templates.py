from pytenable_was.user_templates import UserTemplatesAPI

def test_user_templates_api_initialization(http_client):
    api = UserTemplatesAPI(http_client)
    assert hasattr(api, "list_user_templates")
