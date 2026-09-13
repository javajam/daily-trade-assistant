from dta_bot import killswitch


def test_file_pause_and_resume(tmp_path, monkeypatch):
    monkeypatch.delenv(killswitch.ENV_FLAG, raising=False)
    path = tmp_path / "KILL"
    assert not killswitch.is_active(str(path))
    killswitch.pause(str(path))
    assert path.exists()
    assert killswitch.is_active(str(path))
    assert "file" in (killswitch.reason(str(path)) or "")
    assert killswitch.resume(str(path)) is True
    assert not killswitch.is_active(str(path))


def test_env_flag(monkeypatch, tmp_path):
    monkeypatch.setenv(killswitch.ENV_FLAG, "1")
    path = tmp_path / "missing"
    assert killswitch.is_active(str(path))
    assert killswitch.ENV_FLAG in (killswitch.reason(str(path)) or "")
