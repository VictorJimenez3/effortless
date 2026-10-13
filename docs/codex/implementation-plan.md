> Current update: delegated cost optimization added a guarded Luna-low judge and a warm Sol-high cache bypass; see [total usage](total-usage.md). The original plan below documents the earlier quality-first implementation.

# Codex Effortless implementation plan

**Goal:** Compare judges fairly, install real automatic effort selection for Codex desktop, and publish the implementation in the fork.

**Architecture:** Transparent stdio adapter, isolated native judge, conservative Sol worker policy, reversible local installation.

**Tech stack:** Python 3.11+ standard library, native Codex app-server, macOS launch environment.

**Spec:** `docs/codex/design.md`. Execution is inline under the user's explicit instruction to finish setup.

## Constraints

- Preserve permissions, instructions, input, original binary, and manual model/effort choices.
- No new API key or subscription; no prompt text in logs; ephemeral judge threads.
- Winner: correctness/override acceptance first, then median latency.
- No automatic downgrade from Sol to Luna or automatic Astra escalation in the initial installation.
- Do not terminate ongoing desktop chats; clearly report the one-time restart requirement.

## Tasks

1. Freeze and run the matched comparison, publish its exact protocol and scored results. Confirm identical prompts/rules and complete paired repetitions.
2. Write failing policy tests for collaboration precedence, unavailable profiles, manual changes, continuations, and preserving unrelated fields. Implement `policy.py`; run the suite green.
3. Write failing transport tests for passthrough, cancelled pending turns, prompt ordering, malformed/timeout judge output and large frames. Implement native RPC judge and transparent proxy; run the suite green.
4. Verify the proxy against the real native Codex backend, including actual effective model/effort, a manual change, and a forced timeout. Implement reversible installer and controller; verify installed paths and status.
5. Run the skill sync and verify discovery or report its concrete dependency. Review the complete changes independently, fix important findings with regression tests, publish source/tests/reports to the fork, and report activation status.

## Review focus

- Native app emits settings notifications; UI feedback must not be misclassified as a manual change.
- A pending judge must not swallow interruption or hold permission responses.
- Different chats can proceed concurrently; successive turns in a chat remain ordered.
- Native JSONL responses may exceed 64 KiB; the adapter must handle large frames.
- Desktop launch override must survive login and uninstall must restore prior user configuration.
