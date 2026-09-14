Artifacts: [run directory](<../../../../../output/experiments/v9-cod-fewshot5-v3-20260912>). Unlinked artifact names below are relative to that directory.

# Fixed random-five CoD few-shot probe

Seed20260912; same five records across three attempts, no resampling. Full meta/documents retained; synthetic demonstrations independent of dev labels. Output512/thinking256/batch5. Format assessment only, not classification/generalization.

Success: native nonempty thinking; both labels; each line <=5 whitespace words including label; ends before budget; valid JSON without retry.

| Attempt | Placement | Success | Body tokens (16,175,111,055,31) |
|---|---|---|---|
| 1 | System | 0/5 | 254, 0, 254, 254, 254 |
| 2 | System and user suffix | 0/5 | 254, 0, 0, 254, 0 |
| 3 | System and user suffix | 1/5 | 0, 254, 55, 254, 106 |

Attempt3 adds explicit termination after both verdicts. Prompt680 Gemma tokens per copy, included twice. PPS-DEV-111 succeeds at55 body tokens. PPS-DEV-31 ends at106 but has a7-word line (6 without label). Two outputs hit254 body/256 budget span; one empty channel. All15 final outputs parse without retries. No lower budget tested/adopted. Partial induction, not reliable enforcement. Core classification prompt unchanged by probe.

Exact prompt: analysis/v9_cod_fewshot5/prompt_v3.txt. Full messages/raw token IDs in run folders.
