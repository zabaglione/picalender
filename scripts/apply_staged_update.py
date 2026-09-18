#!/usr/bin/env python3
"""Apply a verified file manifest on the Pi with backup and automatic rollback.

Run on the Pi: python3 apply_staged_update.py --stage /path/to/candidate
Restore: python3 BACKUP/restore.py --rollback BACKUP
Only manifest files are replaced. Local settings, wallpapers, cache and the
service definition are preserved. The virtual environment is managed separately.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time


def run(*command):
    return subprocess.run(command, check=True, text=True, capture_output=True).stdout.strip()


def service(action):
    run("sudo", "-n", "systemctl", action, "picalender.service")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_name(name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Unsafe manifest path")
    if path.parts[0] in (".git", "venv", "cache", "logs", "wallpapers") or name == "settings.yaml":
        raise ValueError("Protected application path")


def wait_for_service():
    previous_pid, stable = None, 0
    for _ in range(20):
        time.sleep(1)
        state = run("systemctl", "show", "picalender.service", "-p", "ActiveState", "-p", "MainPID")
        values = dict(line.split("=", 1) for line in state.splitlines())
        pid = values.get("MainPID")
        stable = stable + 1 if values.get("ActiveState") == "active" and pid != "0" and pid == previous_pid else 0
        previous_pid = pid
        if stable >= 5:
            return pid
    raise RuntimeError("Service did not reach a stable running state")


def validate_backup(backup, metadata):
    for name, record in metadata["files"].items():
        verify_name(name)
        if record["existed"]:
            source = backup / "files" / name
            if digest(source) != record["old_sha256"]:
                raise RuntimeError("Backup checksum mismatch: " + name)


def restore_files(backup, metadata):
    validate_backup(backup, metadata)
    app = Path(metadata["app"])
    for name, record in metadata["files"].items():
        target = app / name
        if record["existed"]:
            source = backup / "files" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif target.is_file():
            target.unlink()


def rollback(backup):
    metadata = json.loads((backup / "deployment.json").read_text())
    validate_backup(backup, metadata)
    service("stop")
    restore_files(backup, metadata)
    service("start")
    pid = wait_for_service()
    print(f"Restored previous application. PID={pid}")


def apply(stage):
    app = Path.home() / "picalender"
    manifest = json.loads((stage / "deploy_manifest.json").read_text())
    for name, expected in manifest["files"].items():
        verify_name(name)
        source = stage / name
        if source.is_symlink() or digest(source) != expected:
            raise RuntimeError("Staged checksum mismatch: " + name)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = Path.home() / "picalender-backups" / (manifest["release"] + "-" + stamp)
    backup.mkdir(parents=True)
    metadata = {"app": str(app), "release": manifest["release"], "files": {}, "status": "prepared"}
    for name, new_hash in manifest["files"].items():
        target = app / name
        if target.is_symlink():
            raise RuntimeError("Refusing to replace a symlink: " + name)
        existed = target.exists()
        metadata["files"][name] = {"existed": existed, "new_sha256": new_hash,
                                   "old_sha256": digest(target) if existed else None}
        if existed:
            previous = backup / "files" / name
            previous.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, previous)
    if (app / "settings.yaml").exists():
        shutil.copy2(app / "settings.yaml", backup / "settings.yaml.reference")
    shutil.copy2(Path(__file__), backup / "restore.py")
    (backup / "service.reference").write_text(run("systemctl", "cat", "picalender.service") + "\n")
    (backup / "deployment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Backup: " + str(backup), flush=True)
    service("stop")
    try:
        for name in manifest["files"]:
            target = app / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(stage / name, target)
        service("start")
        metadata["pid"] = wait_for_service()
        metadata["status"] = "running"
    except Exception:
        service("stop")
        restore_files(backup, metadata)
        service("start")
        wait_for_service()
        metadata["status"] = "rolled_back"
        (backup / "deployment.json").write_text(json.dumps(metadata, indent=2) + "\n")
        raise
    (backup / "deployment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Applied verified update. PID=" + metadata["pid"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stage", type=Path)
    group.add_argument("--rollback", type=Path)
    args = parser.parse_args()
    if args.rollback:
        rollback(args.rollback.resolve())
    else:
        apply(args.stage.resolve())


if __name__ == "__main__":
    main()
