# Matched stricter-rules judge comparison

October 13, 2026. This replaces the preliminary Luna-low judge recommendation in the earlier report.

Both candidates received the exact same frozen stricter policy, output schema, and 34 examples three times each. Twenty-two examples have independently checked worker outcomes; twelve test complex context, manual choices, confirmations, ambiguous requests, and quoted prompt injection. The judge never sees the scoring key. For the 22 worker tasks, a choice is accepted only if that selected profile passed every recorded execution of that task; the other 12 use declared profile/action acceptance rules. The complete scoring key and worker pass counts are published with the results. Calls were paired serially and candidate order alternated.

The selection rule was fixed before running: correctness and override handling first, then median single-prompt latency as a tiebreaker.

| Judge | Accepted settings decisions | Median latency |
|---|---:|---:|
| gpt-6-luna · low | 101/102 | 2.83s |
| gpt-6.1-sol · low | 102/102 | 4.82s |

**Selected judge: GPT-6.1 Sol at low reasoning.** Luna was faster, but made one unacceptable effort choice: medium for a database deadlock and data-loss problem where the acceptance policy required Sol-extra-high or Astra-high. Sol had no rejected choices in this sample.

These are 34 distinct examples repeated three times, not 102 distinct tasks. The one-choice difference does not establish a universal or statistically decisive model ranking. It does determine the installation under the declared quality-first rule. No dollar savings are claimed.

The initial implementation automatically adjusts effort on Sol. It does not downgrade the worker to Luna or automatically escalate to Astra. Explicitly selected models, maximum/Ultra effort, and manual picker changes are preserved. Timeouts and invalid/unavailable choices preserve the original request.

See [full protocol and results](paired-judge-results.json), the [initial evaluation](evaluation-report.md), and [Codex installation instructions](../../codex-port/README.md).
