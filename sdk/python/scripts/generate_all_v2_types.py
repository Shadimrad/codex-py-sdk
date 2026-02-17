#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    schema_dir = repo.parent.parent / "codex-rs" / "app-server-protocol" / "schema" / "json" / "v2"
    out_dir = repo / "src" / "codex_app_server" / "generated" / "v2_all"

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "datamodel-codegen",
            "--input",
            str(schema_dir),
            "--input-file-type",
            "jsonschema",
            "--output",
            str(out_dir),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.10",
        ],
        check=True,
    )

    (out_dir / "__init__.py").touch()
    print(f"wrote {out_dir}")


if __name__ == "__main__":
    main()
