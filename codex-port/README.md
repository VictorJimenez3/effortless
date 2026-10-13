# Effortless for Codex desktop

An experimental macOS adapter for automatic Codex reasoning effort, built in a fork of [HeyCubit's original Effortless](https://github.com/HeyCubit/effortless). The Claude plugin remains intact.

The [matched evaluation](../docs/codex/matched-comparison.md) selected **GPT-6.1 Sol at low reasoning as the judge**: 102/102 accepted choices versus Luna-low's 101/102, using the same 34 examples three times with identical stricter rules. These results are a small benchmark, not a correctness guarantee or proof of savings. The later [matched cost sample](../docs/codex/cost-comparison.md) found that the current Sol judge made Auto about 35% more expensive than fixed Sol-high across six synthetic tasks; worker savings alone did not cover the judge.

## Install

Requirements: macOS, Python 3.11+, the ChatGPT/Codex desktop app, the Codex CLI, and an existing ChatGPT sign-in. No new API key is required.

Clone this fork, then run with a Python 3.11+ interpreter:

```sh
python3 codex-port/install.py --judge gpt-6.1-sol
```

If the system `python3` is older, use an installed newer interpreter, or `uv run --python 3.12 codex-port/install.py --judge gpt-6.1-sol` if you already use uv.

**Quit and reopen the desktop app once after installation.** Ongoing chats are not terminated by the installer. A per-user login service preserves the executable override on subsequent logins. The original signed app, original Codex executable, permissions and native configuration stay unchanged.

## What happens

The desktop app starts the adapter through its existing `CODEX_CLI_PATH` override. The adapter relays the original Codex app-server protocol and asks an isolated native judge to classify each new main-chat prompt. It changes actual top-level and collaboration-mode effort fields before the main turn starts.

The initial automatic worker is **GPT-6.1 Sol**, with low, medium or extra-high effort. Suggested Luna work maps to Sol-low; suggested Astra work maps to Sol-extra-high. Automatic model switching remains disabled because the unrestricted worker downgrades failed the earlier evaluation and switching a warm chat loses cached context. Manually selected other models and maximum/Ultra effort are preserved.

The native model picker wins: a manual model/effort change disables Auto in that chat. Bare confirmations preserve the active effort. Interrupts, permission replies and other messages pass immediately. A judge failure, timeout, malformed output or unavailable choice forwards the original request. The worker receives the complete original input. Prompts with attachments retain their original effort because the text judge cannot evaluate those attachments.

Only main-chat `turn/start` messages on the local desktop stdio connection are routed. Native subagent turns, cloud/remote connections, ordinary terminal Codex sessions and non-stdio transports are not automatically routed. Other CLI commands are delegated to the original Codex binary. This version has no custom composer bar or cache countdown; use the native model picker and the controller status.

## Controls

With `~/.local/bin` on PATH:

```sh
effortless-codex status
effortless-codex auto off
effortless-codex auto on
effortless-codex judge gpt-6.1-sol
effortless-codex judge gpt-6-luna
effortless-codex launch
effortless-codex uninstall
```

An explicit-only `$effortless-codex` controller skill is also installed. Auto on resumes routing after manual overrides. `auto: true` is a saved setting; `adapter_active: true` confirms a live adapter process. Changing Auto/judge does not require a restart once the adapter is active.

Settings: `~/.config/effortless-codex/settings.json`. Runtime and local status: `~/.local/share/effortless-codex/`. Status contains model/effort and outcome metadata; it does not store prompts, assistant replies or judge explanations. The judge uses an auth alias to the existing native library, not a copied credential. Native ephemeral judge history is not saved to rollouts.

Uninstall restores the prior executable override if the current override still belongs to this adapter, removes unmodified managed launch files and the controller skill, and keeps edited files and local runtime files for recovery. It does not remove the original Codex app or authentication. On systems with a separate personal skill synchronization service, run that service after installing/removing the controller skill; it must not copy provider credentials or connections.

## Verify

```sh
PYTHONPATH=codex-port python3 -m unittest discover -s codex-port/tests -v
```

The suite covers collaboration precedence, permission preservation, manual overrides, timeouts, cancellation, request ordering, malformed messages, large protocol responses and installer collisions. Live validation additionally checked actual native effort changes, preserving effort on a confirmation, a manual picker change and forced timeout against the app's real bundled backend. The installed adapter passed all four probes; [recorded results](../docs/codex/native-validation.json) and [verification details](../docs/codex/verification.md) are included.

To run the synthetic live smoke test against your installed adapter (uses your existing login and model usage):

```sh
python3 codex-port/scripts/live_validation.py --adapter "$HOME/.local/bin/effortless-codex"
```

The executable override is a desktop integration point observed in the installed app rather than a stable public plugin API. App updates may require compatibility testing. This adapter does not require the Claude plugin's function-hook runtime and does not pretend prompt instructions alone can change effort.
