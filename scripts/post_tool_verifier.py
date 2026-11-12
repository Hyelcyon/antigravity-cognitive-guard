#!/usr/bin/env python3
"""PostToolUse Syntax & Verification State Tracker for Antigravity Agent.

Executes immediate syntax validation on modified files (Python, JSON, TOML) and tracks
whether verification commands have been executed during the current active session.
"""

import json
import os
from pathlib import Path
import py_compile
import re
import sys

try:
    import tomllib
except ImportError:
    tomllib = None

STATE_DIR = Path(os.environ.get("PLUGIN_DATA", str(Path(__file__).resolve().parent)))
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / ".session_tracker.json"

VERIFICATION_COMMAND_PATTERNS = [
    r"\bpytest\b",
    r"\bpython\s+-m\s+unittest\b",
    r"\bpython\s+-m\s+py_compile\b",
    r"\b(pnpm|npm|yarn|bun)\s+(test|run\s+test|run\s+check)\b",
    r"\b(vitest|playwright|cypress|jest)\b",
    r"\bcargo\s+(test|check|clippy)\b",
    r"\b(mvn|gradle)\s+test\b",
    r"\bdotnet\s+test\b",
    r"\b(ctest|make\s+test)\b",
    r"\bgo\s+test\b",
    r"\b(selene|luau-analyze)\b",
    r"\b(tsc|ruff|mypy|eslint|biome)\b",
    r"\baudit_skills\b",
    r"\bverify_\w+\b",
    r"\bgit\s+(diff|status)\b",
]


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


def verify_file_syntax(file_path_str: str) -> bool:
    if not file_path_str:
        return True
    p = Path(file_path_str)
    if not p.is_file():
        return True

    ext = p.suffix.lower()
    if ext == ".py":
        try:
            py_compile.compile(str(p), doraise=True)
            return True
        except py_compile.PyCompileError:
            return False
    elif ext == ".json":
        try:
            with p.open("r", encoding="utf-8") as f:
                json.load(f)
            return True
        except Exception:
            return False
    elif ext == ".toml" and tomllib:
        try:
            with p.open("rb") as f:
                tomllib.load(f)
            return True
        except Exception:
            return False

    return True


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        payload = {}

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    state = load_state()

    if tool_name in ["edit_file", "write_file"]:
        target_path = args.get("Path", "")
        if target_path:
            verify_file_syntax(target_path)
            if target_path not in state["modified_files"]:
                state["modified_files"].append(target_path)
            state["verified"] = False
            state["warnings_issued"] = 0
            save_state(state)

    elif tool_name == "run_command":
        cmd = args.get("CommandLine", "")
        if any(re.search(pat, cmd, re.IGNORECASE) for pat in VERIFICATION_COMMAND_PATTERNS):
            state["verified"] = True
            save_state(state)

    json.dump({}, sys.stdout)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
