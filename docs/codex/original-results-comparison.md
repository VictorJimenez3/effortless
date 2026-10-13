# Original project versus the Codex cost probe

Reviewed October 13, 2026, against the original project's current published [benchmark report](https://github.com/HeyCubit/effortless/blob/main/bench/RESULTS.md).

The original Claude benchmark used four coding tasks, three repetitions per setup, Opus 5.5 and Sonnet 5.5, and four effort/Auto conditions: 96 runs total. It used fresh repository copies and API-priced usage. All 12 tasks in each model/condition passed its checks.

| Original main model | Constant high cost/task | Auto cost/task | Reported reduction |
|---|---:|---:|---:|
| Opus 5.5 | $0.209 | $0.149 | 29% |
| Sonnet 5.5 | $0.107 | $0.096 | 10% |

The figures exclude the stated $0.001–$0.002 judge fee per prompt. Adding that stated fee yields roughly 28% savings for Opus-high and 8–9% for Sonnet-high. These are calculations from the author's reported averages, not independently repeated Claude measurements. Mostly easy tasks, few repeats, fresh chats, and API pricing limit their generality.

The original identifies fewer model requests as the major saving: Opus fell from 8.0 requests/task at high to 5.8 with Auto. The tasks included inspecting repository files, adding comments, writing/running a script, and tracing a multi-file flow.

Our 1.6% Codex estimate included the judge, but used six self-contained single-answer tasks with no tools, one pair each. It does not test whether lower effort reduces model/tool cycles in a real repository workflow. Earlier Codex experiments included two tool-enabled fixtures, but those did not provide a matched fixed-high versus Auto cost comparison. The percentages therefore are not a meaningful head-to-head Claude/Codex comparison.

The current recommendation is native Sol-high with Auto off for daily use. Both Codex arms passed all six cost tasks; the small observed saving does not establish a reliability benefit, a stable production saving, or a lower included-plan allowance debit. The experimental adapter remains installed and published. A representative matched repository benchmark, including judge, all model requests, tool use, retries and cache behavior, would be required before recommending Auto as a cost-saving default.

The original also leaves worker-model switching off by default because refilling another model's cache can erase the apparent saving. The Codex adapter likewise keeps the worker on Sol.
