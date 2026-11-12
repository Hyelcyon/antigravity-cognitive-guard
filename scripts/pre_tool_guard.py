#!/usr/bin/env python3
"""Operational Safety PreToolUse Guard for Antigravity Agent.

Intercepts tool execution (primarily run_command) to enforce operational safety invariants:
blocking catastrophic filesystem operations, unverified force-pushes, and credential leaks.
"""

import json
import re
import sys
from typing import Tuple

CATASTROPHIC_PATTERNS = [
    (r"rmdir\s+/[sS]\s+/[qQ]\s+[cC]:\\?$", "Root drive recursive deletion attempt"),
    (r"format\s+[a-zA-Z]:", "Disk formatting command attempt"),
    (r"del\s+/[fF]\s+/[sS]\s+/[qQ]\s+[cC]:\\windows", "Windows system directory deletion attempt"),
    (r"rm\s+-rf\s+/(?:\s|$)", "Root directory recursive deletion attempt"),
    (r"git\s+push\s+(?:.*)?--force", "Forced git push to remote repository"),
    (r"git\s+reset\s+--hard\s+head~[2-9]\d*", "Destructive multi-commit hard reset"),
    (r"(?:type|cat|Get-Content)\s+.*(?:\.env|id_rsa|id_ed25519|\.pem)\b", "Direct secret/credential dump attempt"),
]


def evaluate_command_safety(command_line: str) -> Tuple[bool, str]:
    normalized = command_line.strip()
    for pattern, description in CATASTROPHIC_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
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

    output = {"decision": "allow"}
    json.dump(output, sys.stdout)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
