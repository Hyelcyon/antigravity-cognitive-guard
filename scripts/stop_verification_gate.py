#!/usr/bin/env python3
"""Autonomous Verification Stop Gate for Antigravity Agent.

Intercepts the agent when it attempts to finish execution without running tests or
verification commands on newly written or edited source/configuration files.
Exempts pure documentation and artifact edits from mandatory test gates.
"""

import json
import os
from pathlib import Path
import sys

STATE_DIR = Path(os.environ.get("PLUGIN_DATA", str(Path(__file__).resolve().parent)))
STATE_FILE = STATE_DIR / ".session_tracker.json"

CODE_CONFIG_EXTENSIONS = {
    ".py", ".ts", ".js", ".tsx", ".jsx", ".rs", ".go", ".java",
    ".cpp", ".c", ".h", ".cs", ".luau", ".lua", ".json", ".yaml",
    ".yml", ".toml", ".sql", ".sh", ".ps1", ".bat"
}


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"modified_files": [], "verified": True, "warnings_issued": 0}


def save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


def filter_executable_modifications(files: list) -> list:
    return [f for f in files if Path(f).suffix.lower() in CODE_CONFIG_EXTENSIONS]


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        payload = {}

    termination_reason = payload.get("terminationReason", "")
    state = load_state()

    code_modifications = filter_executable_modifications(state.get("modified_files", []))
    has_unverified_code_modifications = (
        bool(code_modifications)
        and not state.get("verified", True)
        and state.get("warnings_issued", 0) < 1
    )

    if termination_reason == "NO_TOOL_CALL" and has_unverified_code_modifications:
        state["warnings_issued"] = state.get("warnings_issued", 0) + 1
        save_state(state)
        modified_summary = ", ".join(Path(f).name for f in code_modifications[:3])
        output = {
            "decision": "continue",
            "reason": (
                f"[Autonomous Verification Gate] Code/config files modified ({modified_summary}) without execution verification. "
                "Per workstation quality standards, you must execute test, build, or syntax verification commands "
                "and confirm results before declaring the task complete."
            )
        }
        json.dump(output, sys.stdout)
        sys.stdout.flush()
        return

    state["modified_files"] = []
    state["verified"] = True
    state["warnings_issued"] = 0
    save_state(state)

    output = {"decision": "allow"}
    json.dump(output, sys.stdout)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
