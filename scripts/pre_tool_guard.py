#!/usr/bin/env python3
"""Operational Safety PreToolUse Guard for Antigravity Agent.

Intercepts tool execution (run_command, write_file, edit_file) to enforce operational safety invariants:
blocking catastrophic filesystem operations, system path modification, unverified force-pushes,
package registry pollution, and direct secret dumping.
"""

import json
from pathlib import Path
import re
import sys
from typing import Tuple

CATASTROPHIC_COMMAND_PATTERNS = [
    (r"rmdir\s+/[sS]\s+/[qQ]\s+[a-zA-Z]:\\?$", "Root drive recursive deletion attempt"),
    (r"format\s+[a-zA-Z]:", "Disk formatting command attempt"),
    (r"del\s+/[fF]\s+/[sS]\s+/[qQ]\s+[a-zA-Z]:\\windows", "Windows system directory deletion attempt"),
    (r"Remove-Item\s+.*(?:-Recurse|-r).*(?:[a-zA-Z]:\\|\$env:SystemRoot)", "PowerShell root/system recursive deletion attempt"),
    (r"\b(?:Clear-Disk|Initialize-Disk|Format-Volume)\b", "PowerShell disk manipulation attempt"),
    (r"rm\s+-(?:r[fF]|fr)\s+/(?:\s|$|\*)", "Root directory recursive deletion attempt"),
    (r"\bmkfs(?:\.\w+)?\b", "Filesystem creation attempt"),
    (r"\bdd\s+if=.*of=/dev/(?:sd[a-z]|nvme|hd[a-z])", "Direct block device overwrite attempt"),
    (r"chmod\s+-R\s+777\s+/(?:\s|$)", "Root permission compromise attempt"),
    (r"git\s+push\s+.*(?:--force|-f\b|\+[\w\d_/-]+:)", "Forced git push to remote repository"),
    (r"git\s+reset\s+--hard\s+head~[2-9]\d*", "Destructive multi-commit hard reset"),
    (r"git\s+clean\s+-[xX]*f[xX]*d*", "Destructive untracked git cleanup"),
    (r"(?:npm|pnpm|yarn|cargo|gem)\s+publish\b", "Unauthorized package registry publish attempt"),
    (r"(?:type|cat|Get-Content|head|tail|more)\s+.*(?:\.env|id_rsa|id_ed25519|\.pem|credentials\.json|\.aws/credentials)\b", "Direct secret/credential dump attempt"),
]

PROTECTED_PATH_PATTERNS = [
    (r"^[a-zA-Z]:\\(?:Windows|System32)\b", "Windows system directory"),
    (r"^/(?:etc|bin|sbin|usr/bin|usr/sbin|System)\b", "Root system directory"),
    (r"[\\/]\.git[\\/]hooks\b", "Git hook tampering"),
]


def evaluate_command_safety(command_line: str) -> Tuple[bool, str]:
    normalized = command_line.strip()
    for pattern, description in CATASTROPHIC_COMMAND_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return False, description
    return True, ""


def evaluate_path_safety(file_path: str) -> Tuple[bool, str]:
    if not file_path:
        return True, ""
    try:
        resolved = str(Path(file_path).resolve())
    except Exception:
        resolved = file_path

    for pattern, description in PROTECTED_PATH_PATTERNS:
        if re.search(pattern, resolved, re.IGNORECASE):
            return False, description
    return True, ""


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        payload = {}

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    if tool_name == "run_command":
        command_line = args.get("CommandLine", "")
        is_safe, reason = evaluate_command_safety(command_line)
        if not is_safe:
            output = {
                "decision": "deny",
                "reason": f"[Operational Safety Interceptor] Command blocked: {reason}."
            }
            json.dump(output, sys.stdout)
            sys.stdout.flush()
            return

    elif tool_name in ["write_file", "edit_file"]:
        target_path = args.get("Path", "")
        is_safe, reason = evaluate_path_safety(target_path)
        if not is_safe:
            output = {
                "decision": "deny",
                "reason": f"[Operational Safety Interceptor] File modification blocked: {reason} ({target_path})."
            }
            json.dump(output, sys.stdout)
            sys.stdout.flush()
            return

    output = {"decision": "allow"}
    json.dump(output, sys.stdout)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
