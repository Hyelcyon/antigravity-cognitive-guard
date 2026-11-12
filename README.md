# Antigravity Cognitive Guard

Deterministic Level-1 operational safety and verification lifecycle guard plugin for Google Antigravity agents.

---

## 1. Overview

**Antigravity Cognitive Guard** implements a lightweight, zero-latency Level-1 interception layer designed to:
- **Prevent Catastrophic Operations**: Intercepts and blocks dangerous filesystem, disk, and secret-dump commands before execution (`PreToolUse`).
- **Enforce Verification Invariants**: Tracks source and configuration modifications and requires actual verification commands (tests, builds, linters) before the agent can declare a task finished (`PostToolUse` and `Stop`).
- **Eliminate Runtime Slop & Invariant Duplication**: Avoids slow, synchronous prompt injection inside `PreInvocation`, deferring cognitive invariants to static rule files.

---

## 2. Architecture & Lifecycle Hooks

```
[Agent Action Loop]
       │
       ├──► PreToolUse (pre_tool_guard.py)
       │      └─ Blocks destructive operations (rmdir /s /q, format, secret dumps)
       │
       ├──► PostToolUse (post_tool_verifier.py)
       │      ├─ Immediate AST syntax checks on edited Python / JSON files
       │      └─ Tracks modified files vs executed verification commands
       │
       └──► Stop (stop_verification_gate.py)
              └─ Intercepts premature stops if files were modified without verification
```

---

## 3. Installation

Clone directly into your Antigravity plugins directory:

```bash
git clone https://github.com/Hyelcyon/antigravity-cognitive-guard.git ~/.gemini/config/plugins/antigravity-cognitive-guard
```

Alternatively, add it as a submodule or link the repository to your active plugins directory.

---

## 4. Running Tests

```bash
python -m unittest tests/test_guard_hooks.py
```

---

## 5. License

MIT License. See [LICENSE](./LICENSE) for details.
