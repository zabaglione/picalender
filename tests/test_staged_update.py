import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from scripts import apply_staged_update as deploy


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.setattr(deploy.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(deploy, "run", lambda *args: "service reference")
    monkeypatch.setattr(deploy, "service", Mock())
    monkeypatch.setattr(deploy, "wait_for_service", lambda: "123")
    app, stage = tmp_path / "picalender", tmp_path / "candidate"
    app.mkdir(); stage.mkdir()
    (app / "main.py").write_text("previous")
    (app / "settings.yaml").write_text("private configuration")
    (app / "user-file.txt").write_text("keep")
    files = {"main.py": "updated", "new-module.py": "added"}
    for name, content in files.items():
        (stage / name).write_text(content)
    (stage / "deploy_manifest.json").write_text(json.dumps({
        "release": "test", "files": {name: hashlib.sha256(content.encode()).hexdigest()
                                      for name, content in files.items()}}))
    return app, stage, tmp_path


def test_apply_and_restore_preserve_local_configuration(prepared):
    app, stage, root = prepared
    deploy.apply(stage)
    assert (app / "main.py").read_text() == "updated"
    backup = next((root / "picalender-backups").iterdir())
    deploy.rollback(backup)
    assert (app / "main.py").read_text() == "previous"
    assert not (app / "new-module.py").exists()
    assert (app / "settings.yaml").read_text() == "private configuration"
    assert (app / "user-file.txt").read_text() == "keep"


def test_failed_start_restores_previous_files(prepared, monkeypatch):
    app, stage, root = prepared
    monkeypatch.setattr(deploy, "wait_for_service", Mock(side_effect=[RuntimeError("start failed"), "456"]))
    with pytest.raises(RuntimeError, match="start failed"):
        deploy.apply(stage)
    assert (app / "main.py").read_text() == "previous"
    assert not (app / "new-module.py").exists()
    backup = next((root / "picalender-backups").iterdir())
    assert json.loads((backup / "deployment.json").read_text())["status"] == "rolled_back"


def test_checksum_mismatch_does_not_stop_service(prepared):
    _, stage, _ = prepared
    (stage / "main.py").write_text("unexpected change")
    with pytest.raises(RuntimeError, match="checksum"):
        deploy.apply(stage)
    deploy.service.assert_not_called()


def test_corrupt_backup_does_not_stop_running_service(prepared):
    _, stage, root = prepared
    deploy.apply(stage)
    backup = next((root / "picalender-backups").iterdir())
    (backup / "files/main.py").write_text("corrupted")
    deploy.service.reset_mock()
    with pytest.raises(RuntimeError, match="checksum"):
        deploy.rollback(backup)
    deploy.service.assert_not_called()


@pytest.mark.parametrize("path", ["../escape", "/etc/passwd", ".git/config", "settings.yaml", "venv/replace"])
def test_protected_paths_are_rejected(path):
    with pytest.raises(ValueError):
        deploy.verify_name(path)
