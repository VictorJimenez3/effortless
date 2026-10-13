---
name: effortless-codex
description: Use when the user explicitly asks to inspect, enable, disable, or change the judge of their installed Effortless Codex desktop routing adapter.
---

# Effortless Codex controls

The installed command is `effortless-codex`. This controls the local Codex adapter; it does not change Devin's own model or reasoning settings.

- Read current installation, Auto setting, judge and active backend: `effortless-codex status`.
- Enable Auto or resume after a manual picker choice: `effortless-codex auto on`.
- Disable Auto: `effortless-codex auto off`.
- Change judge: `effortless-codex judge gpt-6.1-sol` or `effortless-codex judge gpt-6-luna`.
- Launch the desktop app with the adapter: `effortless-codex launch`.
- Remove this installation when explicitly requested: `effortless-codex uninstall`.

Confirm mutations by reading status. `auto: true` is a saved setting; only `adapter_active: true` confirms a live adapter process. An already open desktop app needs one quit/reopen after initial installation. Do not terminate ongoing chats to force activation. Ordinary CLI commands and unsupported transports are delegated to the original Codex executable.

The initial policy automatically adjusts Sol effort and preserves manual model choices. It does not automatically downgrade work to Luna or promote it to Astra. Never claim guaranteed correctness, savings, a cache countdown, or automatic routing of subagents.
