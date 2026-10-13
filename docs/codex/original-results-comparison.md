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


## Luna and Sol against a constant model/effort

The roles must be separated. The original uses Haiku 5.5 to judge effort and to compact chats, while Opus/Sonnet still do the main work. Switching the main worker to Haiku is an experimental option, off by default. Our Codex adapter uses Luna for judging and Sol for work; it does not implement the original's cheap compaction or handoff UI.

| Codex approach | Observed cost versus its fixed Sol-high baseline | What the evidence establishes |
|---|---|---|
| Constant Sol-high, no judge | Baseline | Straightforward daily-use choice; no classification overhead. |
| Sol worker with variable effort + Sol-low judge | About 35% more | Six matched single-answer pairs, all correct; helper overhead exceeded the worker reduction. |
| Sol worker with variable effort + Luna-low judge | About 1.6% less | A separate cohort of six matched pairs, all correct; too small to establish a worthwhile general saving. |
| Constant Sol-low, no judge | No matched production percentage measured | Passed all 22 distinct self-contained text tasks; removes judge overhead, but large workflows and cache effects still need evaluation. |
| Luna-low as main worker | Much cheaper token rates, not an established reliable replacement | Passed 16/22 distinct tool-free tasks; failed calculations and validation. Both small tool-enabled repository fixtures passed, but that is too little evidence for general automatic switching. |

In the latest Luna-judge cohort, the Sol worker alone cost 4.3% less than fixed high. The judge used most of that reduction, leaving 1.6% net. Worker input and aggregate cache-hit counts matched in this cohort; per-case cache hits differed. These cost estimates use Standard paid-credit rates, not observed account debits or included plan allowance.

Luna's uncached-input and output token rates are 95% lower than GPT-6.1 Sol's; its cached-input rate is 90% lower. That explains why it makes more sense as the helper than Sol. It does **not** mean changing the main worker to Luna automatically saves 95% per successfully completed task: different token counts, retries and lost cache reuse affect the result. [Official Codex token rates](https://learn.chatgpt.com/docs/pricing#token-rates).

The raw judge comparison was Sol-low 102/102 accepted versus Luna-low 101/102. A conservative code guard addresses the known Luna miss; replaying old decisions through that guard is not a new model accuracy score. Neither model's small judge test establishes a reliable production cost saving.

For daily work, keep Sol-high in the native picker with Auto off. For clearly bounded routine work, a fresh Sol-low chat is a reasonable candidate to try because it avoids the judge call and changing the effort of a long, warm high chat. Reserve Luna as a worker for tasks whose result can be checked cheaply, such as literal extraction. These are scoped recommendations, not guarantees on unseen work. The experimental adapter remains available for representative tool-using cost evaluation.
