# Effortless for Codex: routing experiment
Victor Jimenez — October 13, 2026

This is a completed experiment, not an installed automatic router. It uses the existing Codex ChatGPT login and synthetic inputs. No OpenAI API key was created and no production Codex settings were changed.

## What was tested

- 283 recorded live model requests; three earlier smoke requests and two aborted metadata/transport probes are excluded from the scored results.
- Four judge settings: GPT-6 Luna low and medium, GPT-6.1 Sol low, and GPT-6 Astra low.
- 32 routing scenarios, each judged twice by all four settings: 256 decisions. The scenarios cover simple work, substantial coding, hidden high-consequence context, short follow-ups, explicit overrides, ambiguous tasks, and quoted prompt injection.
- 12 scenarios also judged individually by Luna low, Luna medium, and Sol low: 36 single-prompt decisions.
- 14 independently checkable tasks across eight execution settings: 112 primary task runs. The tasks cover arithmetic, extraction, time zones, SQL NULL behavior, intervals, graph distances, probability, combinatorial counting, optimization, pure Python functions, and modular arithmetic.
- 35 repeats on representative math and code tasks across the original five execution settings.
- The three cheaper judge settings also selected execution profiles for all 14 solved tasks, twice each: 84 decisions. These predictions are compared with actual execution results, not only hand-written routing labels.
- 12 paired Luna judge calls issued sequentially, three live model/effort setting probes, and nine long-context continuity/cache calls, including repeated effort changes.
- Six additional tool-enabled Codex runs: two disposable Python repositories, each repaired by Luna-low, Sol-low and Sol-medium. Independent tests check the finished code after the agent stops.
- Eight fresh held-out tasks: 24 executions across Luna-low, Sol-low and Sol-medium, plus 16 routing decisions made before seeing the new execution results. This tests a calibrated policy developed only from the earlier failures.
- 536 deterministic adapter-contract scenarios: 10 profile/precedence checks, 26 invalid-result/override/fallback cases, and 500 randomized checks preserving permissions and unrelated fields.

The original routing labels are a human-authored acceptance policy, not proof of which model is cheapest or most capable. Actual task correctness is a separate measure. Reasoning tests used isolated ephemeral Codex threads with no model tools or delegation; up to three calls ran concurrently. Controls/cache probes use temporary saved threads in the isolated experiment home because ephemeral threads cannot be resumed from rollouts. Follow-up execution profiles used a randomized order. Paired judge calls were issued sequentially, but the separate tool-enabled fixture client could overlap them. Latency comparisons describe this run rather than a service guarantee.

## Primary task results

| Execution profile | Passed | Median latency | Slowest | Output tokens |
|---|---:|---:|---:|---:|
| astra_high | 14/14 | 5.56s | 19.89s | 2,467 |
| astra_medium | 14/14 | 5.89s | 17.64s | 2,153 |
| luna_low | 10/14 | 2.87s | 5.17s | 946 |
| luna_medium | 10/14 | 3.62s | 9.70s | 2,938 |
| luna_xhigh | 13/14 | 4.17s | 42.48s | 8,704 |
| sol_low | 14/14 | 5.20s | 15.24s | 1,911 |
| sol_medium | 14/14 | 6.22s | 21.32s | 2,486 |
| sol_xhigh | 14/14 | 5.78s | 74.22s | 6,249 |

Primary-task misses:

- luna_low, t03: `{"expected": "2026-12-31 19:05", "actual": "2027-01-01 16:05"}`
- luna_low, t08: `{"expected": 98950096, "actual": 53798080}`
- luna_low, t09: `{"expected": 33, "actual": 31}`
- luna_xhigh, t09: `{"expected": 33, "actual": 32}`
- luna_low, t14: `{"expected": 591, "actual": 370}`
- luna_medium, t10: `{"expected": 51, "actual": 52}`
- luna_medium, t03: `{"expected": "2026-12-31 19:05", "actual": "2027-01-01 16:05"}`
- luna_medium, t05: `{"expected": [[1, 5], [8, 12], [12, 13]], "actual": [[1, 5], [8, 13]]}`
- luna_medium, t12: `{"pass": false, "detail": "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit"}`

## Repeat results

| Profile | Passed repeats | Missed task ids |
|---|---:|---|
| astra_high | 7/7 | none |
| luna_low | 3/7 | t13, t09, t14, t08 |
| luna_xhigh | 7/7 | none |
| sol_medium | 7/7 | none |
| sol_xhigh | 7/7 | none |

Generated pure functions completed 2,082 successful individual edge-case checks. Graph tests include 120 seeded randomized graphs per implementation; parser/version tests include malformed input, Unicode, cycles, duplicate edges and 5,000-digit components. A generation that fails early does not contribute an inferred number of remaining checks.

## Judge results

| Judge | Acceptable profile choices | Full output-policy matches | Solo median | Solo p95 estimate |
|---|---:|---:|---:|---:|
| gpt-6-luna low | 76/76 | 72/76 | 2.96s | 3.43s |
| gpt-6-luna medium | 76/76 | 69/76 | 2.96s | 3.89s |
| gpt-6.1-sol low | 76/76 | 76/76 | 4.55s | 5.70s |
| gpt-6-astra low | 64/64 | 64/64 | not measured | not measured |

The full-policy score also requires the exact route/keep/manual action. Some failures are choosing keep when the selected profile equals the current profile; these do not by themselves choose the wrong model. This is a reason to enforce state-handling rules outside the model. All structured output validation errors and request errors are retained in the raw data.

Paired sequential Luna latency:

| Judge effort | Calls | Median | Slowest |
|---|---:|---:|---:|
| low | 6 | 2.66s | 2.96s |
| medium | 6 | 3.12s | 3.64s |

## Tool-enabled Codex fixture results

| Fixture | Model and effort | Independent checks | Latency | Recorded command/tool items |
|---|---|---|---:|---:|
| schedule | gpt-6-luna low | passed | 10.18s | 3 |
| schedule | gpt-6.1-sol low | passed | 27.28s | 3 |
| schedule | gpt-6.1-sol medium | passed | 33.80s | 3 |
| decode | gpt-6-luna low | passed | 14.18s | 3 |
| decode | gpt-6.1-sol low | passed | 28.33s | 2 |
| decode | gpt-6.1-sol medium | passed | 35.03s | 3 |

Scheduling uses 120 seeded randomized cases checked by exhaustive enumeration, an input-mutation check, and a 2,000-job case. The decoder has 19 independent valid/malformed/Unicode cases. Supplied visible tests are preserved; final code is checked by the separate runner. Tool-free misses can be recoverable when the agent is allowed to execute calculations or tests. These two repository fixtures are still too small to establish reliability on real multi-service work.

## Did the judge select settings that actually passed?

| Judge | Selected a profile passing every observed run of that task | Selected an observed failing profile |
|---|---:|---:|
| gpt-6-luna low | 17/28 | t08→luna_low, t09→luna_low, t12→luna_medium, t14→luna_low, t03→luna_low, t03→luna_medium, t05→luna_medium, t08→luna_low, t10→luna_medium, t12→luna_medium, t14→luna_low |
| gpt-6-luna medium | 17/28 | t03→luna_low, t08→luna_low, t09→luna_low, t12→luna_medium, t14→luna_low, t03→luna_low, t05→luna_medium, t08→luna_low, t10→luna_medium, t12→luna_medium, t14→luna_low |
| gpt-6.1-sol low | 23/28 | t03→luna_medium, t05→luna_medium, t12→luna_medium, t03→luna_medium, t05→luna_medium |

This conservative comparison counts a profile as reliable for a task only if it passed all recorded runs of that task. It is a small sample, not a production success-rate estimate. The judge did not receive the answer key or execution results.

## Calibrated policy on fresh held-out tasks

After the first comparison, the revised Luna-low judge policy sets Sol-low as the minimum for exact calculations, dates/time zones, algorithmic work and executable code. Luna-low remains eligible for straightforward literal extraction and simple nontechnical wording. More complex work can choose Sol-medium or above. The held-out questions and answers were not used to write that policy.

| Worker setting | Passed fresh tasks |
|---|---:|
| luna_low | 6/8 |
| sol_low | 8/8 |
| sol_medium | 8/8 |

The calibrated Luna-low judge selected a worker setting that passed the fresh task in 16/16 decisions. This is two decisions each on eight distinct tasks, not sixteen distinct tasks and not a guarantee on unseen work.

## Recommended initial model access

- Judge: GPT-6 Luna at low reasoning. Heavier judge settings did not cure the unsafe downgrades without calibration. Enforce the allowed model menu and state/override handling in code, and treat model-reported confidence as uncalibrated.
- Main worker: keep the selected main model by default. With the default Sol family, permit low for well-defined work, medium for substantial work, and extra-high for difficult work. Sol-low and Sol-medium passed all 22 distinct self-contained tasks tested here; larger workflows remain untested.
- Luna as a worker: permit straightforward extraction/wording in short or fresh chats. It also passed both tool-enabled repository fixtures, so verified bounded coding is worth a separate optional savings mode. Do not assume short exact calculations or algorithms are safe to downgrade.
- Astra: keep it available for explicit selection or an opted-in escalation path for exceptionally demanding work. This small benchmark did not demonstrate an Astra advantage over Sol on the tested tasks, so automatic Astra escalation is not empirically established.
- Start with these three current model families. Older generations and GPT-Reserve were not tested and should not be added automatically. Leave maximum/Ultra reasoning out of the initial automatic menu; this experiment did not evaluate their benefits, latency, or delegation behavior. Preserve explicit manual model/effort choices.
- Model switching should be a separate option from effort adjustment. Use measured conversation length/cache behavior and known task requirements; failures, timeouts, invalid output, unavailable choices or uncertainty preserve the existing model/effort.

## Actual Codex controls

| Probe | Effective settings after the turn | Result |
|---|---|---|
| plain | `{"model": "gpt-6-luna", "reasoningEffort": "low"}` | completed |
| mode_precedence | `{"model": "gpt-6-astra", "reasoningEffort": "high"}` | completed |
| mode_rewritten | `{"model": "gpt-6-luna", "reasoningEffort": "low"}` | completed |

Codex collaboration-mode settings can override the top-level model and effort. An adapter must update both locations while preserving collaboration instructions, approval policy, sandbox, cwd and input. The contract probe verifies that only model/effort fields change. Manual selections, disabled Auto, bare follow-ups, malformed results, low confidence, timeouts, unavailable profiles and non-turn-start requests preserve the original request.

## Conversation continuity and cache

| Transition | Effective model/effort | Input tokens | Cached input | Latency | Reference recall |
|---|---|---:|---:|---:|---|
| prime_sol | `{"model": "gpt-6.1-sol", "reasoningEffort": "medium"}` | 29,631 | 0 | 3.91s | prime |
| same_model | `{"model": "gpt-6.1-sol", "reasoningEffort": "medium"}` | 29,655 | 29,440 | 1.81s | passed |
| effort_change | `{"model": "gpt-6.1-sol", "reasoningEffort": "low"}` | 29,686 | 0 | 2.22s | passed |
| switch_luna | `{"model": "gpt-6-luna", "reasoningEffort": "low"}` | 29,956 | 7,936 | 1.35s | passed |
| back_to_sol | `{"model": "gpt-6.1-sol", "reasoningEffort": "low"}` | 30,226 | 29,568 | 3.38s | passed |
| stay_low_repeat | `{"model": "gpt-6.1-sol", "reasoningEffort": "low"}` | 30,742 | 30,080 | 5.29s | passed |
| change_medium_repeat | `{"model": "gpt-6.1-sol", "reasoningEffort": "medium"}` | 30,773 | 29,440 | 2.27s | passed |
| stay_medium_repeat | `{"model": "gpt-6.1-sol", "reasoningEffort": "medium"}` | 30,804 | 30,592 | 2.08s | passed |
| change_low_repeat | `{"model": "gpt-6.1-sol", "reasoningEffort": "low"}` | 30,835 | 30,592 | 2.16s | passed |

These are observed cache-hit counts on one synthetic long-context sequence. They do not establish a guaranteed cache lifetime or a general switching penalty. No countdown is inferred. Both cache behavior and continuity must be verified for the actual Codex backend rather than imported from Claude.

The first Sol→Luna switch reused only 7,936 of 29,956 input tokens; the preceding same-Sol turn reused 29,440 of 29,655. Repeated effort changes later reused most of the prefix, although the first effort-change probe had no cached input. This supports separating model switching from effort adjustment and keeping an already warm main model stable by default. It does not establish guaranteed cache preservation or a dollar saving.

Two harness defects were found and repaired during the control probes: resume requires a saved rollout, and the default Python transport reader rejected a response longer than 64 KiB. Judge trials stay ephemeral; continuity trials are saved only in the isolated experiment home. The reader accepts up to 16 MiB and the affected cache sequence was rerun. These defects are excluded from model-quality scoring and remain disclosed here.

## What this experiment cannot establish

- It does not measure real subscription billing or prove any dollar/percentage savings. Token telemetry and measured latency are provided. ChatGPT plan consumption is not interchangeable with published API prices.
- Twenty-two distinct text-only self-contained tasks and two small repository fixtures are not representative of a large repository, visual design, cross-app work, sustained security investigations, novel proofs or real production incidents. Astra advantages on those tasks remain untested.
- Disabling tools in the reasoning tests may penalize a model that would normally run a calculation or a test to check its work. The tool-enabled fixtures explore this distinction; the results should not be collapsed into a single general model score.
- Extra-high and high runs are not guaranteed to be monotonic in correctness or speed. The measured runs should not be turned into a universal model ranking.
- Confidence is model-reported and uncalibrated. A high confidence value does not prove the selected model will succeed.
- The contract probe is a throwaway test adapter. It is not an installed desktop interception service. Automatic routing, a desktop status bar, restart recovery and a production judge sidecar are not yet installed.

## Sources and reproducibility

- [Original Effortless project](https://github.com/HeyCubit/effortless)
- [OpenAI model selection guidance](https://developers.openai.com/api/docs/guides/model-selection)
- [Codex app-server and per-turn controls](https://developers.openai.com/codex/app-server)
- [Codex hooks and their output contract](https://learn.chatgpt.com/docs/hooks)

The accompanying JSON contains all synthetic prompts, acceptance labels, expected task answers, model outputs, validation failures, token telemetry and measured request times. No account credentials or private user documents are included.
