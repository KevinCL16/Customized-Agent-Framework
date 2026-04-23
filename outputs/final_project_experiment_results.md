# Final Project Experiment Results

## 2026-04-23

### gpt-5.4-mini Reproduction

Primary metric: `combined @ gpt-5.4`

| Setting | legacy@gpt-4o | rubric@gpt-4o | combined@gpt-4o | legacy@gpt-5.4 | rubric@gpt-5.4 | combined@gpt-5.4 |
| --- | --- | --- | --- | --- | --- | --- |
| direct | 62.29 | 82.18 | 72.23 | 59.16 | 74.19 | 66.67 |
| cot | 61.78 | 82.61 | 72.31 | 60.23 | 75.15 | 67.65 |
| default | 67.46 | 85.40 | 76.72 | 64.18 | 78.93 | 71.56 |

Observations:

- `default` is best under both evaluators.
- Under the headline metric, `default` beats `direct` by `+4.88` and `cot` by `+3.90`.
- `cot` is only slightly above `direct` on this run (`+0.98` under `combined@gpt-5.4`).

Notes:

- Reproduction evals are complete for all three settings.
- Reproduction generation still has residual failed examples with no final image: `direct` missing `5`, `cot` missing `7`, `default` missing `0`.
- Per project convention for this run, examples with no final image are treated as failed generations rather than re-run indefinitely.

### Existing gpt-5.4-mini CapImagine Run Check

Workspace checked: `workspace_matplotbench_gpt54mini_capimagine_full`

Status:

- generation not fully complete: `1` missing final image (`example_42`)
- evaluation not fully complete: `20` missing logs under both `gpt-4o` and `gpt-5.4`

Current partial combined scores from that workspace:

| Setting | combined@gpt-4o | combined@gpt-5.4 | Status |
| --- | --- | --- | --- |
| capimagine (partial old workspace) | 83.87 | 79.86 | partial / not frozen |

Notes:

- This older CapImagine workspace is not a complete frozen full-100 run, so these numbers should not be treated as the final paper result.
- Missing-log report from the current aggregate pass is larger than the strict evaluation-gap count because `average_score_calc.py` also flags some ids where one judge track is absent even if the other exists.
- A standardized rerun should use the final-project runner workspace naming and current OpenAI routing patch.

### gpt-5.4-mini CapImagine

Using the existing full workspace with targeted backfill:

- workspace: `workspace_matplotbench_gpt54mini_capimagine_full`
- evaluation gaps: `0` under both `gpt-4o` and `gpt-5.4`
- residual generation failure: `1` missing final image (`example_42`)

| Setting | legacy@gpt-4o | rubric@gpt-4o | combined@gpt-4o | legacy@gpt-5.4 | rubric@gpt-5.4 | combined@gpt-5.4 |
| --- | --- | --- | --- | --- | --- | --- |
| capimagine | 68.79 | 84.95 | 76.70 | 64.86 | 80.11 | 72.49 |

Comparison against the reproduced `default` setting:

| Comparison | combined@gpt-4o | combined@gpt-5.4 |
| --- | --- | --- |
| default | 76.72 | 71.56 |
| capimagine | 76.70 | 72.49 |
| delta (capimagine - default) | -0.02 | +0.93 |

Observations:

- Under `combined@gpt-5.4`, `capimagine` is currently `+0.93` above `default`.
- Under `combined@gpt-4o`, `capimagine` is effectively tied with `default` (`-0.02`).
- Legacy and rubric both move upward relative to the reproduced `default` row under `gpt-5.4`, but the gain is modest rather than dramatic on the full set.

Notes:

- The workspace is evaluation-complete, but not generation-complete: `example_42` still has no final image and is therefore treated as a failed generation.
- `average_score_calc.py` still reports two missing ids (`47`, `69`) on the `gpt-4o` rubric/combined aggregate pass even though the stricter log-presence check now reports zero evaluation gaps; keep that inconsistency in mind when quoting exact denominators.

### gpt-5.4-mini Bucket Analysis

Objective:

- compare `default` vs `capimagine`
- bucket by the reproduced `default` workflow's legacy score
- report where CapImagine helps or regresses on the full set

#### Primary readout: buckets by `gpt-5.4`

| Bucket | Count | default combined@gpt-5.4 | capimagine combined@gpt-5.4 | Delta |
| --- | --- | --- | --- | --- |
| 0-20 | 4 | 27.23 | 38.00 | +10.77 |
| 20-40 | 17 | 45.46 | 57.34 | +11.88 |
| 40-60 | 20 | 62.44 | 62.63 | +0.19 |
| 60+ | 59 | 85.17 | 82.53 | -2.64 |
| Overall | 100 | 71.56 | 72.49 | +0.93 |

Interpretation:

- The full-set gain under `combined@gpt-5.4` comes almost entirely from the hard half of the benchmark.
- CapImagine is strongly helpful in the low buckets:
  - `0-20`: `+10.77`
  - `20-40`: `+11.88`
- It is roughly neutral in the middle bucket (`40-60`: `+0.19`).
- It regresses on the already-strong `60+` bucket (`-2.64`), which explains why the full-set gain remains modest.

Additional signal under `gpt-5.4`:

- `0-20` bucket:
  - legacy delta: `+10.50`
  - rubric delta: `+11.05`
- `20-40` bucket:
  - legacy delta: `+15.24`
  - rubric delta: `+8.52`
- `60+` bucket:
  - legacy delta: `-5.15`
  - rubric delta: `-0.13`

This suggests CapImagine mainly improves difficult examples by recovering structure and task compliance, while sometimes over-editing or drifting on easier examples that the default workflow already gets mostly right.

#### Robustness view: buckets by `gpt-4o`

| Bucket | Count | default combined@gpt-4o | capimagine combined@gpt-4o | Delta |
| --- | --- | --- | --- | --- |
| 0-20 | 7 | 26.50 | 41.64 | +15.14 |
| 20-40 | 7 | 56.21 | 80.71 | +24.50 |
| 40-60 | 9 | 62.00 | 65.58 | +3.58 |
| 60+ | 77 | 84.22 | 80.94 | -3.28 |
| Overall | 100 | 76.72 | 76.70 | -0.02 |

Interpretation:

- `gpt-4o` tells the same bucket story as `gpt-5.4`: strong gains on hard cases, regressions on easy cases.
- The difference is weighting: `gpt-4o` is slightly less favorable overall because the large `60+` bucket penalty nearly cancels the hard-case gains.

Artifacts:

- `outputs/gpt54mini_default_vs_capimagine_buckets_by_gpt54.json`
- `outputs/gpt54mini_default_vs_capimagine_buckets_by_gpt4o.json`
