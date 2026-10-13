# Total usage with judge and cache accounted for

October 13, 2026. The current default uses **Luna-low as judge and Sol as the automatic worker**, with a conservative risk floor and a bypass for a long, warm Sol-high chat. Automatic worker model swapping stays off.

The new six-task comparison used 115,892 raw tokens including the judge, versus 57,322 for constant Sol-high: about 102.2% more raw tokens. At Standard paid-credit rates, the total was 2.79732 versus 2.84314 credits: **about 1.6% lower**, with both approaches passing 6/6. The small saving is not a general performance or subscription-usage guarantee.

## Every measured component

| Component, six tasks | Uncached input | Cached input | Output incl. reasoning | Total raw tokens | Estimated credits |
|---|---:|---:|---:|---:|---:|
| Constant Sol-high | 47,616 | 7,936 | 1,770 | 57,322 | 2.84314 |
| Auto Sol worker | 47,616 | 7,936 | 1,286 | 56,838 | 2.72214 |
| Luna-low judge | 24,904 | 33,792 | 358 | 59,054 | 0.07518 |
| Auto including judge | 72,520 | 41,728 | 1,644 | 115,892 | 2.79732 |

Cached tokens are a subset of input, not extra tokens. Reasoning is a subset of output, not extra output: fixed high used 1,103 reasoning tokens, the Auto worker 621, and the judge 0. These counts have already been included once. All six paired tasks completed without retries, tools, or worker model changes; those components therefore add zero in this sample. The judge reads about 10,000 input tokens per task because the native harness includes context beyond its short visible classification.

The worker input and aggregate cached input totals matched across the two arms in this new sample. Per-case cache hits differed. The worker saved 484 output/reasoning tokens; its 0.12100-credit reduction covered the 0.07518-credit helper overhead by a thin margin. [Full results, telemetry and protocol](luna-cost-comparison-results.json).

The earlier [Sol-judge comparison](cost-comparison.md) was a separate cohort and cost about 35% more than its own fixed-high baseline. Do not compare absolute totals between cohorts as if they shared the same cache state. The earlier accuracy comparison remains valid: raw Sol-low judge decisions scored 102/102 and raw Luna-low 101/102. Changing the default now reflects the full usage objective, not a reversal of those raw scores.

## Current behavior

- The main worker stays on Sol. Changing the separate judge does not swap the model holding the main chat history.
- A valid routing recommendation is raised to Sol-extra-high when bounded recent text contains one of the specified risk terms: data loss, deadlock, double charges, authentication/authorization bypass, remote code execution, or privilege escalation, including common inflections and RCE. This addresses the known Luna effort miss. The guard is lexical and conservative: it can over-escalate benign discussion of those terms and can miss risks expressed differently. It does not guarantee risk detection. Manual choices, invalid/unavailable recommendations and timeout fallbacks retain their existing behavior.
- A chat already using Sol-high skips the judge and preserves high if its latest usage shows at least 16,000 cached input tokens and at least 85% cache reuse, except for the recognized risk terms. These thresholds are an explicit conservative policy choice, not a learned optimum or a cache lifetime guarantee. Warm low/medium chats still allow classification so difficult work can escalate.
- Replaying the previous 102 recorded Luna decisions through the new guard and existing Sol worker floor yields 102/102 accepted effective choices. This is **offline replay**, not a new 102/102 model accuracy result. [Replay detail](guard-replay.json).
- All 51 automated checks passed. Six live native probes passed, including enforced extra-high effort for a risk case and preserving a warm Sol-high chat without a judge call. Permissions remained read-only/never-approve in those probes. [Live results](luna-native-validation.json).

## Interpretation and limits

Total raw tokens alone do not determine cost. Luna and Sol have different rates, and cached input is cheaper than uncached input. Standard credit rates per million uncached input / cached input / output are Sol: 50 / 2.5 / 250; Luna: 2.5 / 0.25 / 12.5. These paid-credit rates do not translate directly into a percentage of included plan allowance. Fast/Ultrafast speeds have different multipliers; the adapter preserves the user's speed settings. [Official pricing](https://learn.chatgpt.com/docs/pricing#token-rates).

The matched cost sample contains the same six synthetic tasks as before: arithmetic, time zones, intervals, scheduling optimization, version comparison code, and a nested decoder. Runs were paired serially with alternating worker order, fresh worker threads, no tools, and one pair per task. It does not establish costs for larger repositories, retries after failed work, delegation, long conversations, or other speed modes. Cache/effort transitions can change input reuse even with the main model fixed. One earlier development probe stopped before workers ran due to a temporary local code error; its discarded judge call is not included in the six scored pairs. One-time development/evaluation usage and this conversation's own usage are separate from the per-task adapter comparison.

The warm-cache bypass was validated separately on a synthetic long conversation; the six-pair percentage does not include that bypass. Its expected benefit is avoiding the helper call while retaining the user's existing high baseline, not an independently established percentage saving. Existing desktop processes still need one quit/reopen to load the updated installed adapter.
