#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _python_sdk_root() -> Path:
    return _repo_root() / "sdk" / "python"


def _platform_tokens() -> tuple[str, list[str]]:
    sys_name = platform.system().lower()
    machine = platform.machine().lower()

    if sys_name == "darwin":
        os_tokens = ["darwin", "apple-darwin", "macos"]
    elif sys_name == "linux":
        os_tokens = ["linux", "unknown-linux"]
    elif sys_name.startswith("win"):
        os_tokens = ["windows", "pc-windows", "win"]
    else:
        raise RuntimeError(f"Unsupported OS: {sys_name}")

    if machine in {"arm64", "aarch64"}:
        arch_tokens = ["aarch64", "arm64"]
    elif machine in {"x86_64", "amd64"}:
        arch_tokens = ["x86_64", "amd64"]
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    return sys_name, [*os_tokens, *arch_tokens]


def _pick_release(channel: str) -> dict:
    releases = json.loads(
        subprocess.check_output(
            ["gh", "api", "repos/openai/codex/releases?per_page=50"],
            text=True,
        )
    )

    if channel == "stable":
        candidates = [r for r in releases if not r.get("prerelease") and not r.get("draft")]
    else:
        candidates = [r for r in releases if r.get("prerelease") and not r.get("draft")]

    if not candidates:
        raise RuntimeError(f"No {channel} release found")

    return candidates[0]


def _pick_asset(release: dict, tokens: list[str]) -> dict:
    assets = release.get("assets", [])
    scored: list[tuple[int, dict]] = []

    for asset in assets:
        name = (asset.get("name") or "").lower()
        if not (name.endswith(".tar.gz") or name.endswith(".zip")):
            continue
        score = sum(1 for t in tokens if t in name)
        if "codex" not in name:
            continue
        scored.append((score, asset))

    if not scored:
        raise RuntimeError("Could not find matching release asset for this platform")

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def _download(url: str, out: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "codex-python-sdk-updater"})
    with urllib.request.urlopen(req) as resp, out.open("wb") as f:
        shutil.copyfileobj(resp, f)


def _extract_binary(archive: Path, out_bin: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if archive.name.endswith(".tar.gz"):
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(tmp)
        elif archive.name.endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(tmp)
        else:
            raise RuntimeError(f"Unsupported archive format: {archive}")

        candidates = [p for p in tmp.rglob("*") if p.is_file() and p.name == "codex"]
        if not candidates:
            raise RuntimeError("No `codex` binary found in downloaded archive")

        out_bin.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidates[0], out_bin)
        mode = out_bin.stat().st_mode
        out_bin.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update pinned Codex release binary + regenerate Python SDK types")
    parser.add_argument("--channel", choices=["stable", "alpha"], default="stable")
    args = parser.parse_args()

    if shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI (`gh`) is required")

    sdk_root = _python_sdk_root()
    bin_path = sdk_root / "bin" / "codex"

    _, tokens = _platform_tokens()
    release = _pick_release(args.channel)
    asset = _pick_asset(release, tokens)

    print(f"Selected release: {release.get('tag_name')} ({args.channel})")
    print(f"Selected asset: {asset.get('name')}")

    with tempfile.TemporaryDirectory() as td:
        archive = Path(td) / (asset.get("name") or "codex-release.tar.gz")
        _download(asset["browser_download_url"], archive)
        _extract_binary(archive, bin_path)

    print(f"Pinned binary updated: {bin_path}")

    env = os.environ.copy()
    env["CODEX_APP_SERVER_BIN"] = str(bin_path)

    # Keep generators aligned with current protocol schema in repo.
    _run(["python3", "scripts/generate_protocol_typed_dicts.py"], cwd=sdk_root)
    _run(["python3", "scripts/generate_types_from_schema.py"], cwd=sdk_root)

    # Optional heavier generator (requires datamodel-codegen in env).
    try:
        subprocess.run(
            ["python3", "scripts/generate_all_v2_types.py"],
            cwd=str(sdk_root),
            check=True,
            env=env,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Skipped generate_all_v2_types.py: {exc}")

    print("Done.")


if __name__ == "__main__":
    main()
