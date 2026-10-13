> Current setup: the later [total-usage evaluation](total-usage.md) changed the default to guarded Luna-low as judge with Sol as worker and a warm-cache bypass. Historical results below remain unchanged.

# Codex adapter verification

Verified October 13, 2026, on macOS using desktop bundled Codex 0.162.0-alpha.17.2 and native judge CLI 0.162.1. Python 3.12.13; standard library only.

- Matched judges: 204 live calls, the same 34 examples three times per judge. Sol-low 102/102 accepted; Luna-low 101/102. The identical frozen protocol, complete results and scoring key are in `paired-judge-results.json`.
- Adapter tests: 43 passing checks. Coverage includes permission/instruction preservation, collaboration precedence, manual changes during and after submission, explicit Auto resumption, judge changes, confirmations, delegated threads, attachments, cancellation before and after native acknowledgement, timeouts, malformed settings/messages, large protocol responses, native process termination, symlink collisions and preserving user edits during uninstall.
- Independent read-only review found lifecycle and installation edge cases. Each material finding was addressed with regression tests, including failures observed before the fixes. The complete suite passed after those fixes.
- Installed adapter: four live probes passed against the actual bundled backend. A request with high effort in both top-level and collaboration-mode settings became Sol-low; a bare confirmation stayed low; a manual medium choice stayed medium; a forced judge timeout preserved high. All probes retained never-approve/read-only permissions. Results are in `native-validation.json`.
- Installation: the launcher delegates ordinary CLI commands to the original bundled executable; saved Auto is on and judge is Sol-low. The per-user login service exited successfully and the launch environment points to the adapter. The controller skill passed its format validator. The existing Codex/Devin sync ran, and Devin's loader discovered the controller with user-only activation.

The already running desktop app was not terminated. One quit/reopen is required for it to start the installed adapter. Configuring a future launch and verifying the installed adapter separately do not prove that an existing desktop backend has changed.

These checks do not establish guaranteed correctness, cost savings, a statistically decisive model ranking, compatibility with future app releases, or routing of cloud connections and native subagents. The automatic worker remains Sol; only its reasoning effort changes. The desktop executable override is an observed integration point rather than a stable public plugin API.
