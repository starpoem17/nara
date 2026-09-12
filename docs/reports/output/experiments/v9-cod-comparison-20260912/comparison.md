Artifacts: [run directory](<../../../../../output/experiments/v9-cod-comparison-20260912>). Unlinked artifact names below are relative to that directory.

# v9/v19: OFF vs Thinking ON vs CoD ON

Same current feature criteria and dev200. Both new ON arms use total512 / thinking256, batch16; CoD adds42 input tokens. OFF reused. Zero-shot adaptation; not a reproduction of paper few-shot experiments.

| Mode | Item | F1 | Precision | Recall | TP | FP | FN |
|---|---|---:|---:|---:|---:|---:|---:|
| off | v9 | 0.4444 | 0.2857 | 1.0000 | 6 | 15 | 0 |
| off | v19 | 0.3636 | 0.4000 | 0.3333 | 2 | 3 | 4 |
| on | v9 | 0.4000 | 0.2632 | 0.8333 | 5 | 14 | 1 |
| on | v19 | 0.4000 | 0.3333 | 0.5000 | 3 | 6 | 3 |
| cod | v9 | 0.4167 | 0.2778 | 0.8333 | 5 | 13 | 1 |
| cod | v19 | 0.5263 | 0.3846 | 0.8333 | 5 | 8 | 1 |

Thinking summaries:

```json
{
  "on": {
    "first_response": {
      "thinking_content_tokens": {
        "n": 200,
        "mean": 254.0,
        "min": 254,
        "median": 254.0,
        "p90": 254.0,
        "p95": 254.0,
        "max": 254,
        "sum": 50800
      },
      "total_tokens": {
        "n": 200,
        "mean": 313.775,
        "min": 302,
        "median": 302.0,
        "p90": 341.0,
        "p95": 368.15,
        "max": 512,
        "sum": 62755
      },
      "at_budget_boundary": 200,
      "empty_thinking": 0,
      "unframed_outputs": 0,
      "line_words": {
        "n": 1884,
        "mean": 10.606157112526539,
        "min": 1,
        "median": 8.0,
        "p90": 22.0,
        "p95": 28.84999999999991,
        "max": 143,
        "sum": 19982
      },
      "lines_le5_fraction": 0.4018046709129512,
      "all_lines_le5_records": 0,
      "records_with_korean": 197,
      "count_at_or_below": {
        "64": 0,
        "96": 0,
        "128": 0,
        "192": 0,
        "256": 200
      }
    },
    "all_attempts": {
      "n": 201,
      "thinking_content_tokens": {
        "n": 201,
        "mean": 254.0,
        "min": 254,
        "median": 254.0,
        "p90": 254.0,
        "p95": 254.0,
        "max": 254,
        "sum": 51054
      },
      "at_budget_boundary": 201
    }
  },
  "cod": {
    "first_response": {
      "thinking_content_tokens": {
        "n": 199,
        "mean": 232.30150753768845,
        "min": 0,
        "median": 254.0,
        "p90": 254.0,
        "p95": 254.0,
        "max": 254,
        "sum": 46228
      },
      "total_tokens": {
        "n": 200,
        "mean": 295.855,
        "min": 48,
        "median": 302.0,
        "p90": 351.2,
        "p95": 398.15,
        "max": 512,
        "sum": 59171
      },
      "at_budget_boundary": 182,
      "empty_thinking": 17,
      "unframed_outputs": 1,
      "line_words": {
        "n": 1750,
        "mean": 11.173714285714286,
        "min": 1,
        "median": 8.0,
        "p90": 21.0,
        "p95": 26.0,
        "max": 145,
        "sum": 19554
      },
      "lines_le5_fraction": 0.35428571428571426,
      "all_lines_le5_records": 0,
      "records_with_korean": 179,
      "count_at_or_below": {
        "64": 17,
        "96": 17,
        "128": 17,
        "192": 17,
        "256": 199
      }
    },
    "all_attempts": {
      "n": 206,
      "thinking_content_tokens": {
        "n": 205,
        "mean": 231.69756097560975,
        "min": 0,
        "median": 254.0,
        "p90": 254.0,
        "p95": 254.0,
        "max": 254,
        "sum": 47498
      },
      "at_budget_boundary": 187
    }
  }
}
```

First-response statistics isolate style from retries. Budget boundary includes thought channel label; content token counts use original generated IDs excluding label and delimiters. Outputs lacking channel delimiters are excluded from thinking-length distributions, not counted as thinking. Empty channels have zero body tokens even if the runtime parser returns the thought label. Boundary is inferred from token positions, not an engine forced-stop flag. Nonempty lines are a descriptive proxy for steps; whitespace words, bullet/number prefix removed. Not a semantic step-compliance proof.
