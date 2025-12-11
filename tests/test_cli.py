import subprocess

def test_cli_version():
    out = subprocess.check_output(
        ["pytenable-was", "--version"],
        text=True
    )
    assert "pytenable-was" in out.lower()

def test_cli_help():
    out = subprocess.check_output(
        ["pytenable-was", "--help"],
        text=True
    )
    assert "Usage" in out
    for cmd in ["config", "scans", "templates", "user-templates"]:
        assert cmd in out
