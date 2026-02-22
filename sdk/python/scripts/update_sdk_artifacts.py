#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sdk_root() -> Path:
    return repo_root() / "sdk" / "python"


def schema_dir() -> Path:
    return repo_root() / "codex-rs" / "app-server-protocol" / "schema" / "json" / "v2"


def _is_windows() -> bool:
    return platform.system().lower().startswith("win")


def pinned_bin_path() -> Path:
    name = "codex.exe" if _is_windows() else "codex"
    return sdk_root() / "bin" / name


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def platform_tokens() -> tuple[list[str], list[str]]:
    sys_name = platform.system().lower()
    machine = platform.machine().lower()

    if sys_name == "darwin":
        os_tokens = ["darwin", "apple-darwin", "macos"]
    elif sys_name == "linux":
        os_tokens = ["linux", "unknown-linux", "musl", "gnu"]
    elif sys_name.startswith("win"):
        os_tokens = ["windows", "pc-windows", "win", "msvc", "gnu"]
    else:
        raise RuntimeError(f"Unsupported OS: {sys_name}")

    if machine in {"arm64", "aarch64"}:
        arch_tokens = ["aarch64", "arm64"]
    elif machine in {"x86_64", "amd64"}:
        arch_tokens = ["x86_64", "amd64", "x64"]
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    return os_tokens, arch_tokens


def pick_release(channel: str) -> dict[str, Any]:
    releases = json.loads(
        subprocess.check_output(["gh", "api", "repos/openai/codex/releases?per_page=50"], text=True)
    )
    if channel == "stable":
        candidates = [r for r in releases if not r.get("prerelease") and not r.get("draft")]
    else:
        candidates = [r for r in releases if r.get("prerelease") and not r.get("draft")]
    if not candidates:
        raise RuntimeError(f"No {channel} release found")
    return candidates[0]


def pick_asset(release: dict[str, Any], os_tokens: list[str], arch_tokens: list[str]) -> dict[str, Any]:
    scored: list[tuple[int, dict[str, Any]]] = []
    for asset in release.get("assets", []):
        name = (asset.get("name") or "").lower()
        if "codex" not in name:
            continue
        if not (name.endswith(".tar.gz") or name.endswith(".zip")):
            continue

        os_score = sum(1 for t in os_tokens if t in name)
        arch_score = sum(1 for t in arch_tokens if t in name)
        if os_score == 0 or arch_score == 0:
            continue

        # Prefer more specific OS/arch matches.
        score = os_score * 10 + arch_score
        scored.append((score, asset))

    if not scored:
        raise RuntimeError("Could not find matching release asset for this platform")

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def download(url: str, out: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "codex-python-sdk-updater"})
    with urllib.request.urlopen(req) as resp, out.open("wb") as f:
        shutil.copyfileobj(resp, f)


def extract_codex_binary(archive: Path, out_bin: Path) -> None:
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

        preferred_names = {"codex.exe", "codex"}
        candidates = [
            p for p in tmp.rglob("*") if p.is_file() and (p.name.lower() in preferred_names or p.name.lower().startswith("codex-"))
        ]
        if not candidates:
            raise RuntimeError("No codex binary found in release archive")

        candidates.sort(key=lambda p: (p.name.lower() not in preferred_names, p.name.lower()))

        out_bin.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidates[0], out_bin)
        if not _is_windows():
            out_bin.chmod(out_bin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def update_binary(channel: str) -> None:
    if shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI (`gh`) is required to download release binaries")

    release = pick_release(channel)
    os_tokens, arch_tokens = platform_tokens()
    asset = pick_asset(release, os_tokens, arch_tokens)
    print(f"Release: {release.get('tag_name')} ({channel})")
    print(f"Asset: {asset.get('name')}")

    with tempfile.TemporaryDirectory() as td:
        archive = Path(td) / (asset.get("name") or "codex-release.tar.gz")
        download(asset["browser_download_url"], archive)
        extract_codex_binary(archive, pinned_bin_path())

    print(f"Pinned binary updated: {pinned_bin_path()}")


def generate_v2_all() -> None:
    out_dir = sdk_root() / "src" / "codex_app_server" / "generated" / "v2_all"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "datamodel-codegen",
            "--input",
            str(schema_dir()),
            "--input-file-type",
            "jsonschema",
            "--output",
            str(out_dir),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.10",
        ],
        cwd=sdk_root(),
    )
    (out_dir / "__init__.py").touch()


# ---- protocol_types.py generation ----
def load_schema(name: str) -> dict[str, Any]:
    return json.loads((schema_dir() / f"{name}.json").read_text())


def object_props(schema: dict[str, Any], node: dict[str, Any]) -> tuple[dict[str, Any], set[str]]:
    if "$ref" in node:
        ref = node["$ref"]
        if ref.startswith("#/definitions/"):
            key = ref.split("/")[-1]
            return object_props(schema, schema["definitions"][key])
        raise ValueError(f"unsupported ref: {ref}")
    return node.get("properties", {}), set(node.get("required", []))


def field_type(v: dict[str, Any]) -> str:
    if "$ref" in v:
        ref = v["$ref"]
        if ref.endswith("Thread"):
            return "ThreadObject"
        if ref.endswith("Turn"):
            return "TurnObject"
        if ref.endswith("ThreadTokenUsage"):
            return "ThreadTokenUsage"
        return "dict[str, Any]"
    if "anyOf" in v:
        non_null = [x for x in v["anyOf"] if x.get("type") != "null"]
        if len(non_null) == 1:
            return f"{field_type(non_null[0])} | None"
    t = v.get("type")
    if t == "string":
        return "str"
    if t == "integer":
        return "int"
    if t == "boolean":
        return "bool"
    if t == "array":
        if (v.get("items") or {}).get("$ref", "").endswith("Thread"):
            return "list[ThreadObject]"
        if (v.get("items") or {}).get("$ref", "").endswith("Turn"):
            return "list[TurnObject]"
        return "list[dict[str, Any]]"
    return "dict[str, Any]"


def render_typed_dict(name: str, props: dict[str, Any], req: set[str]) -> str:
    lines = [f"class {name}(TypedDict):"]
    if not props:
        lines.append("    pass")
        return "\n".join(lines)
    for k, v in props.items():
        t = field_type(v)
        if k in req:
            lines.append(f"    {k}: {t}")
        else:
            lines.append(f"    {k}: NotRequired[{t}]")
    return "\n".join(lines)


def generate_protocol_types() -> None:
    out = sdk_root() / "src" / "codex_app_server" / "generated" / "protocol_types.py"
    tsr = load_schema("ThreadStartResponse")
    turs = load_schema("TurnStartResponse")
    ttu = load_schema("ThreadTokenUsageUpdatedNotification")

    thread_props, thread_req = object_props(tsr, tsr["definitions"].get("Thread", {}))
    turn_props, turn_req = object_props(turs, turs["definitions"].get("Turn", {}))
    usage_props, usage_req = object_props(ttu, ttu["definitions"].get("ThreadTokenUsage", {}))

    roots = {
        "ThreadStartResponse": object_props(tsr, tsr),
        "TurnStartResponse": object_props(turs, turs),
        "ThreadTokenUsageUpdatedNotificationParams": object_props(ttu, ttu),
    }

    parts = [
        "from __future__ import annotations",
        "",
        "from typing import Any, NotRequired, TypedDict",
        "",
        "# Generated by scripts/update_sdk_artifacts.py",
        "",
        render_typed_dict("ThreadObject", thread_props, thread_req),
        "",
        render_typed_dict("TurnObject", turn_props, turn_req),
        "",
        render_typed_dict("ThreadTokenUsage", usage_props, usage_req),
        "",
    ]
    for name, (props, req) in roots.items():
        parts.append(render_typed_dict(name, props, req))
        parts.append("")

    out.write_text("\n".join(parts))


# ---- schema_types.py generation ----
TARGET_SCHEMAS = {
    "ThreadStartResponse": "ThreadStartResponse.json",
    "ThreadResumeResponse": "ThreadResumeResponse.json",
    "ThreadReadResponse": "ThreadReadResponse.json",
    "ThreadListResponse": "ThreadListResponse.json",
    "ThreadForkResponse": "ThreadForkResponse.json",
    "ThreadArchiveResponse": "ThreadArchiveResponse.json",
    "ThreadUnarchiveResponse": "ThreadUnarchiveResponse.json",
    "ThreadSetNameResponse": "ThreadSetNameResponse.json",
    "ThreadCompactStartResponse": "ThreadCompactStartResponse.json",
    "TurnStartResponse": "TurnStartResponse.json",
    "TurnSteerResponse": "TurnSteerResponse.json",
    "ModelListResponse": "ModelListResponse.json",
}


@dataclass(slots=True)
class FieldSpec:
    name: str
    annotation: str
    required: bool
    source_expr: str


@dataclass(slots=True)
class ClassSpec:
    name: str
    fields: list[FieldSpec]


def py_type_for_schema(schema: dict[str, Any], defs: dict[str, Any], nested: set[str]) -> tuple[str, str]:
    if "$ref" in schema:
        ref = schema["$ref"].split("/")[-1]
        if ref in nested:
            return ref, "object"
        rd = defs.get(ref, {})
        if rd.get("type") == "string":
            return "str", "scalar"
        if rd.get("type") == "integer":
            return "int", "scalar"
        if rd.get("type") == "boolean":
            return "bool", "scalar"
        return "Any", "scalar"
    t = schema.get("type")
    if t == "string":
        return "str", "scalar"
    if t == "integer":
        return "int", "scalar"
    if t == "boolean":
        return "bool", "scalar"
    if t == "array":
        item_t, _ = py_type_for_schema(schema.get("items", {}), defs, nested)
        return f"list[{item_t}]", "array"
    if t == "object":
        return "dict[str, Any]", "object"
    return "Any", "scalar"


def field_source(field_name: str, py_type: str, kind: str) -> str:
    g = f'payload.get("{field_name}")'
    if py_type == "str":
        return f"str({g} or '')"
    if py_type == "int":
        return f"int({g} or 0)"
    if py_type == "bool":
        return f"bool({g})"
    if kind == "array":
        return f"list({g} or [])"
    return g


def class_from_schema(name: str, schema: dict[str, Any], defs: dict[str, Any], nested: set[str]) -> ClassSpec:
    props = schema.get("properties", {})
    req = set(schema.get("required", []))
    fields: list[FieldSpec] = []
    for n, s in props.items():
        t, k = py_type_for_schema(s, defs, nested)
        fields.append(FieldSpec(name=n, annotation=t, required=n in req, source_expr=field_source(n, t, k)))
    return ClassSpec(name=name, fields=fields)


def generate_schema_types() -> None:
    out = sdk_root() / "src" / "codex_app_server" / "generated" / "schema_types.py"
    raw: dict[str, dict[str, Any]] = {}
    defs: dict[str, Any] = {}
    for cname, fname in TARGET_SCHEMAS.items():
        data = json.loads((schema_dir() / fname).read_text())
        raw[cname] = data
        defs.update(data.get("definitions", {}))

    nested = {"Thread", "Turn"}
    specs: list[ClassSpec] = []
    for n in sorted(nested):
        if defs.get(n):
            specs.append(class_from_schema(n, defs[n], defs, nested))
    for name, root in raw.items():
        specs.append(class_from_schema(name, root, defs, nested))

    parts: list[str] = [
        "# Auto-generated by scripts/update_sdk_artifacts.py",
        "# DO NOT EDIT MANUALLY.",
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from typing import Any, TypedDict",
        "",
    ]
    for spec in specs:
        parts.append(f"class {spec.name}Dict(TypedDict, total=False):")
        if spec.fields:
            for f in spec.fields:
                parts.append(f"    {f.name}: {f.annotation}")
        else:
            parts.append("    pass")
        parts.append("")
        parts.append("@dataclass(slots=True, kw_only=True)")
        parts.append(f"class {spec.name}:")
        if spec.fields:
            for f in spec.fields:
                default = "" if f.required else " = None"
                parts.append(f"    {f.name}: {f.annotation}{default}")
        else:
            parts.append("    pass")
        parts.append("")
    out.write_text("\n".join(parts) + "\n")


def generate_types() -> None:
    # v2_all is the authoritative generated surface.
    generate_v2_all()


def main() -> None:
    parser = argparse.ArgumentParser(description="Single SDK maintenance entrypoint")
    parser.add_argument("--channel", choices=["stable", "alpha"], default="stable")
    parser.add_argument("--types-only", action="store_true", help="Regenerate types only (skip binary update)")
    args = parser.parse_args()

    if not args.types_only:
        update_binary(args.channel)
    generate_types()
    print("Done.")


if __name__ == "__main__":
    main()
