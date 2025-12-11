from pytenable_was.templates import TemplatesAPI

def test_templates_api_initialization(http_client):
    api = TemplatesAPI(http_client)
    assert hasattr(api, "list_all")
    assert hasattr(api, "get")
