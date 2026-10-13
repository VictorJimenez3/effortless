# Cost: automatic effort versus constant Sol-high

Measured October 13, 2026. **The current adapter was about 34.8% more expensive than constant Sol-high on six synthetic tasks after including the Sol-low judge.** Both approaches passed 6/6 independent checks. This supplements the quality comparison; winning that comparison did not establish a cost advantage.

The software adds no subscription fee and uses the existing native ChatGPT sign-in. The judge consumes model usage in addition to the main worker. The monthly plan price does not change just because the adapter is installed.

## Matched sample

Six existing examples: exact arithmetic, a time-zone conversion, half-open intervals, scheduling optimization, strict version comparison code, and a nested decoder. Each task ran once at Sol-high and once at the effort selected by the installed Sol-low judge policy. The worker remained Sol in both arms; run order alternated. Workers used independent fresh threads, synthetic inputs, and no tools. Judge prompts included the same worker task and answer-format instructions, with no answer key. Full returned answers were checked independently.

Both workers used the desktop bundled backend, while the isolated judge used the installed native CLI helper. Auto mapped four tasks to low and two to medium. The adapter policy and guards were called directly by the harness; this is a controlled cost probe, not measurement of an ongoing desktop session. Empty recent context and the observed cache mix limit how broadly it can be applied.

| Setting | Estimated credits, all six tasks | Passed |
|---|---:|---:|
| Constant Sol-high | 3.10685 | 6/6 |
| Auto worker alone | 2.29918 | 6/6 |
| Added Sol-low judge | 1.88883 | — |
| Auto including judge | 4.18801 | 6/6 |

Worker-only consumption fell 26.0%, saving 0.80767 credits. The judge added 1.88883 credits, giving a net increase of 34.8%. Different cache hits contributed to the worker reduction; it cannot all be attributed to reasoning effort.

| Case | Auto effort | Fixed high | Auto worker | Judge | Auto total |
|---|---|---:|---:|---:|---:|
| t01 | low | 0.47450 | 0.47450 | 0.49935 | 0.97385 |
| t03 | low | 0.47720 | 0.09949 | 0.50280 | 0.60229 |
| t05 | low | 0.48820 | 0.47995 | 0.12076 | 0.60071 |
| t09 | medium | 0.50140 | 0.49915 | 0.12271 | 0.62186 |
| t12 | low | 0.55100 | 0.15979 | 0.51410 | 0.67389 |
| t13 | medium | 0.61455 | 0.58630 | 0.12911 | 0.71541 |

All numeric costs above are projections in credits, not measured account debits or percentages of the included plan allowance. [Full results, token counts and protocol](cost-comparison-results.json).

## Pricing and break-even

Standard GPT-6.1 Sol credit rates are 50 credits per million uncached input tokens, 2.5 per million cached input tokens, and 250 per million output tokens, with no separate Codex cache-write charge. Effort does not select a separate per-token price; it influences how much model work is performed. Reasoning tokens are included within output usage, so they must not be added a second time. Sources: [Codex pricing](https://learn.chatgpt.com/docs/pricing#token-rates) and [reasoning effort and token usage](https://developers.openai.com/api/docs/guides/reasoning).

Cost projection = ((input − cached input) × 50 + cached input × 2.5 + output × 250) / 1,000,000.

The judge averaged 0.315 credits per classified task in this new sample. If input/cache usage and other work stayed equal, the worker would need to save approximately 1259 output/reasoning tokens per judged task merely to cover that average overhead. This is a conditional break-even calculation, not a fixed threshold for all chats.

The judge reads roughly 10,000 input tokens per call in this native harness, despite producing a short classification. Cache reuse changes its cost substantially. Bigger tasks can save enough work to offset this overhead; tiny tasks may already use little reasoning even at high effort. The model itself reasons adaptively at different effort settings.

The same recorded usage has a Standard API token-rate equivalent of about $0.124 for fixed high and $0.168 for Auto, using $2/M input, $0.10/M cached input and $10/M output and the recorded zero cache-write counts. These are illustrative API equivalents, **not charges from this installation**. API usage and subscription usage are separate, and credit purchase prices depend on the plan/agreement. [API rate card](https://developers.openai.com/api/docs/pricing).

## Practical implication

Do not advertise this installation as cheaper than fixed Sol-high yet. It has verified routing behavior and a small quality comparison, but the first matched cost sample shows that the judge can erase worker savings. Larger representative tasks, warm conversation sequences, retries, tool use and speed modes need comparison before claiming general savings. Installation settings have been left unchanged by this cost investigation.
