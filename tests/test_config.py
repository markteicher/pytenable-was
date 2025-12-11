from pytenable_was.config import Config

def test_config_cycle(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr(Config, "CONFIG_FILE", cfg_file)

    cfg = Config()
    cfg.set_access_key("A1")
    cfg.set_secret_key("B2")
    cfg.set_proxy("http://proxy")

    loaded = cfg.load()
    assert loaded["access_key"] == "A1"
    assert loaded["secret_key"] == "B2"
    assert loaded["proxy"] == "http://proxy"

    cfg.clear()
    assert cfg.load() == {}
