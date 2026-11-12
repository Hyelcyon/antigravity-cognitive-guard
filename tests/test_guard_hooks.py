#!/usr/bin/env python3
"""Automated Test Suite for Antigravity Cognitive Guard Hooks."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"


class TestGuardHooks(unittest.TestCase):
    def run_hook(self, script_name: str, stdin_data: dict) -> dict:
        script_path = SCRIPTS_ROOT / script_name
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            input=json.dumps(stdin_data),
            capture_output=True,
            text=True,
            cwd=str(PLUGIN_ROOT),
        )
        self.assertEqual(proc.returncode, 0, f"Script {script_name} failed: {proc.stderr}")
        return json.loads(proc.stdout) if proc.stdout.strip() else {}

    def test_pre_tool_guard_allows_safe_command(self):
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "git status"}}}
        output = self.run_hook("pre_tool_guard.py", payload)
        self.assertEqual(output.get("decision"), "allow")

    def test_pre_tool_guard_blocks_catastrophic_deletion(self):
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "rmdir /s /q C:\\"}}}
        output = self.run_hook("pre_tool_guard.py", payload)
        self.assertEqual(output.get("decision"), "deny")
        self.assertIn("Root drive recursive deletion", output.get("reason", ""))

    def test_pre_tool_guard_blocks_secret_dump(self):
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "type .env"}}}
        output = self.run_hook("pre_tool_guard.py", payload)
        self.assertEqual(output.get("decision"), "deny")

    def test_verification_cycle_and_stop_gate(self):
        test_file = PLUGIN_ROOT / "hooks.json"
        edit_payload = {
            "toolCall": {
                "name": "write_file",
                "args": {"Path": str(test_file)}
            }
        }
        res_post = self.run_hook("post_tool_verifier.py", edit_payload)
        self.assertEqual(res_post, {})

        stop_payload = {"terminationReason": "NO_TOOL_CALL"}
        res_stop = self.run_hook("stop_verification_gate.py", stop_payload)
        self.assertEqual(res_stop.get("decision"), "continue")
        self.assertIn("Verification Gate", res_stop.get("reason", ""))

        cmd_payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "pytest tests/"}
            }
        }
        res_post_cmd = self.run_hook("post_tool_verifier.py", cmd_payload)
        self.assertEqual(res_post_cmd, {})

        res_stop_after = self.run_hook("stop_verification_gate.py", stop_payload)
        self.assertEqual(res_stop_after.get("decision"), "allow")


if __name__ == "__main__":
    unittest.main()
