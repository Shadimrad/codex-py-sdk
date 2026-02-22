from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_generated_files_are_up_to_date():
    # Regenerate contract artifacts via single maintenance entrypoint.
    subprocess.run(["python3", "scripts/update_sdk_artifacts.py", "--types-only"], cwd=ROOT, check=True)

    # Ensure no diff in generated targets after regeneration.
    diff = subprocess.run(
        [
            "git",
            "diff",
            "--",
            "src/codex_app_server/generated/schema_types.py",
            "src/codex_app_server/generated/protocol_types.py",
            "src/codex_app_server/generated/v2_all",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert diff.returncode == 0, f"Generated files drifted:\n{diff.stdout}\n{diff.stderr}"
