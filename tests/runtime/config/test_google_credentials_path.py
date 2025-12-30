import pytest

from runtime.config.google_credentials import resolve_google_credentials


def test_google_credentials_missing_fails_fast(tmp_path, monkeypatch):
    # We monkeypatch paths.google_credentials_path to point to a temp location
    import paths as paths_mod

    def _fake():
        return tmp_path / "missing.json"

    monkeypatch.setattr(paths_mod, "google_credentials_path", _fake)

    with pytest.raises(FileNotFoundError):
        resolve_google_credentials()
