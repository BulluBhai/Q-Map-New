# Q-MAP — Combined Scoring and Output Design

**Package document 05 | Version 1.1 | 11-Nov-26 | Status: Proposed — updated for the confirmed Owner decisions OD-02, OD-03 and OD-09; pending ChatGPT review and Project Owner approval**

| Field | Value |
|---|---|
| Covers | Weighted combined score, score calibration, scoring profiles, missing and invalid result policy (options A and B), combined result structure, AI-friendly run output, optional interpretation layer |
| Depends on | Document 04 (scanner results) |
| Prepared by | Claude 2 |

> This package is a design and preparation deliverable. It is not approval to begin production coding.

**Change log**

| Version | Changed sections | Reason |
|---|---|---|
| 1.0 | — | First issue |
| 1.1 | §1, §3.3 | OD-02 is confirmed: the combined score means **Combined Technical Setup Strength**. Stated that it is not a probability, guarantee or recommendation. |
| 1.1 | §4.1 W-6, W-7; §5.5; §6 status table | OD-03 is confirmed: **reject** the combined score when a required result is missing or invalid. Renormalisation (option B) is kept only as the documented, not-adopted alternative; it is not implemented in P1. |
| 1.1 | §8 | Feature statuses updated |

Unchanged in v1.1: §2, §3.1, §3.2, §4.2–§4.4, §5.1–§5.4 (kept as the record of the analysis behind OD-03), §7.

---

## 1. Purpose and boundary

The combined score answers one question: **"Taking the selected scanners together, with the importance I gave each, how strong is the result for this instrument?"** It works like a weighted exam mark.

**Approved scope (blueprint):**
- common 0–100 scale,
- configurable weights totalling 100%,
- every score, weight and contribution visible,
- reproducible,
- deterministic,
- missing results never silently treated as zero.

**What the combined score is not (v1.1).** It is not a probability of profit, a guarantee, a forecast of price direction or an automatic trading recommendation. It measures how strongly a stock satisfies the technical conditions measured by the selected scanners (OD-02). The user remains responsible for decisions (Human-Readable Blueprint §9).

**Deferred:**
- adaptive weights, regime-dependent weights,
- AI-generated weights or scores,
- conditional rules between scanners,
- automated decisions or trade execution.

---

## 2. The formula

For one instrument in one run:

> **Contribution(scanner) = Score(scanner) × Weight(scanner) ÷ 100**
>
> **Combined Score = Σ Contribution(scanner)**

Weights are stored as percentages, e.g. 40 for 40%.

**Worked example** (the blueprint's illustration; scanner names are illustrative only):

| Scanner | Score | Weight | Contribution |
|---|---:|---:|---:|
| Moving Average Analysis | 80 | 40% | 80 × 40 ÷ 100 = **32.00** |
| Pivot Point Analysis | 70 | 35% | 70 × 35 ÷ 100 = **24.50** |
| Momentum Analysis | 60 | 25% | 60 × 25 ÷ 100 = **15.00** |
| **Total** | | **100%** | **71.50** |

**Precision (TC-17):**
- All values are kept at full precision internally and in the JSON.
- Rounding to 2 decimal places happens only for display, using the round-half-up rule that a person expects (0.125 → 0.13).
- The JSON stores the unrounded numbers, so anyone can recompute the result exactly.

---

## 3. Calibration — making different scanners comparable (OD-09 per scanner)

Raw scanner measures are not comparable. A percentage distance, a count of touches and a breakout ratio mean different things. The blueprint therefore requires each scanner to convert its own measure to 0–100 before it can take part in a combined score.

### 3.1 Requirements every scanner calibration must meet

| # | Requirement | Why |
|---|---|---|
| CAL-1 | Defined in the scanner's approved specification, with a calibration version | Reproducibility |
| CAL-2 | States what **0**, **50** and **100** mean, in words | Comparability between scanners |
| CAL-3 | Same **direction** as every other scanner in a profile: higher = more of the property the combined score measures (OD-02) | Otherwise one scanner cancels another |
| CAL-4 | Deterministic, with fixed anchors. Depends only on this instrument's data and the parameters. | The same input always gives the same score |
| CAL-5 | Clipped to [0, 100] | Common range |
| CAL-6 | Must **not** depend on which other instruments are in the same run | A score that changes when you add a stock to the run is not reproducible |
| CAL-7 | Hand-verified examples at 0-side, middle and 100-side values in the specification | Proof the mapping works as written |

### 3.2 Calibration methods

| Method | How it works | Recommendation |
|---|---|---|
| **Fixed-anchor mapping** | The raw measure is mapped linearly between documented anchor values, then clipped. Example: a raw value of −5% maps to 0, 0% to 50 and +5% to 100. | **Recommended default** — simple, transparent, verifiable by hand |
| **Rule-based points** | Points are added for clearly defined conditions (e.g. +25 if condition X), then capped at 100 | Recommended where the scanner is condition-based |
| Frozen reference percentile | The raw value's position within a **saved, version-locked** reference distribution | Possible later (P2): it needs a stored reference set and re-approval whenever that set changes |
| Rank within the current run | Score = position among the instruments in this run | **Not allowed** (breaks CAL-6) |

### 3.3 What "combined score" means (OD-02 — **confirmed**)

**Confirmed meaning (Owner wording):** *Combined Technical Setup Strength measures how strongly a stock satisfies the technical conditions measured by the selected scanners.* Every scoring profile in P1 carries this meaning. The analysis below explains why a profile may include only scanners whose calibration supports it. Still open (document 12, item G-10): which scanners a profile contains and their weights.

A weighted sum is only meaningful if every participating scanner measures the **same kind of thing** in the same direction. For example, "strength of a bullish set-up", or "reliability of the instrument's technical behaviour".

The meaning must be fixed for each scoring profile before scoring is built. A profile may only include scanners whose calibration states that meaning.

**Recommendation:** each scoring profile carries a one-sentence `meaning` field that the owner approves, and each scanner specification declares which meanings it supports.

---

## 4. Scoring profiles (configuration)

Weights are configuration, not code (Approved — blueprint). They are kept in `config/scoring_profiles.json`, which can be edited in Notepad or later from the Analysis Runner.

```json
{
  "profiles_file_version": "1.0",
  "profiles": [
    {
      "profile_id": "example_profile",
      "profile_version": 1,
      "meaning": "Approved one-sentence meaning of a high combined score (OD-02)",
      "missing_result_policy": "REJECT",
      "scanners": [
        {"scanner_id": "scanner_a", "scanner_major_version": 1, "weight": 40},
        {"scanner_id": "scanner_b", "scanner_major_version": 1, "weight": 35},
        {"scanner_id": "scanner_c", "scanner_major_version": 1, "weight": 25}
      ]
    }
  ]
}
```

### 4.1 Validation (run does not start if any check fails)

| Check | Rule |
|---|---|
| W-1 | Weights sum to exactly 100, within 0.0001, after reading |
| W-2 | Every weight is greater than 0 and at most 100 |
| W-3 | No scanner listed twice |
| W-4 | Every scanner is registered and has `produces_score = True` |
| W-5 | The registered scanner's MAJOR version equals `scanner_major_version` (see 4.4) |
| W-6 | `missing_result_policy` is `REJECT` — the only value permitted in P1 (OD-03, confirmed). Any other value, including `RENORMALISE`, makes the profile invalid. |
| W-7 | `meaning` is not empty and states the confirmed OD-02 meaning (Combined Technical Setup Strength) |

Example message: "Scoring profile 'example_profile' weights total 95, but must total 100. Please correct config\scoring_profiles.json."

### 4.2 Reproducibility

Every combined result records:
- the profile ID, profile version, meaning and policy,
- each scanner's ID, full version, score, weight and contribution,
- the data versions used.

From the JSON alone, anyone can recompute the combined score with a calculator.

### 4.3 Scope of combination

In P1, a combined score is calculated only from scanner results produced **in the same run**, for the same instrument, the same analysis window and the same data versions.

Combining results saved from different runs is deliberately not supported. Stale or mismatched results therefore cannot occur by design, and no "staleness" rules are needed.

### 4.4 When a scanner changes

If a scanner's MAJOR version changes (its formula or calibration changed), every profile using it becomes invalid (W-5) until the owner confirms it again. This means updating `scanner_major_version` and increasing `profile_version`. A silently changed meaning cannot then leak into a combined score.

---

## 5. Missing or invalid scanner results (OD-03 — Project Owner decision, blocks M5)

### 5.1 What counts as a valid result

A scanner result can contribute only if **all** of these hold:
- status `OK`,
- score present,
- score finite and within [0, 100],
- the scanner's major version matches the profile.

Anything else is **unavailable**: `INSUFFICIENT_DATA`, `INVALID_DATA`, `NOT_APPLICABLE`, `ERROR`, or failed validation. An unavailable result is **never** treated as a score of zero (Approved — blueprint).

### 5.2 The two options

**Option A — Reject.** If any scanner in the profile has no valid result, no combined score is produced for that instrument. Its status is `REJECTED_MISSING_RESULT` and it lists which scanners were missing and why.

**Option B — Renormalise.** Use the available valid scanners and scale their weights up so they total 100%:

> Combined Score = Σ (Score × Weight) ÷ Σ (Weights of available scanners)

The result is marked `PARTIAL_RENORMALISED`, with the available weight shown (e.g. 75%).

### 5.3 Worked example — Momentum result missing

Same scores and weights as section 2.

| | Option A | Option B |
|---|---|---|
| Calculation | — | (32.00 + 24.50) ÷ 0.75 = 56.50 ÷ 0.75 |
| Combined score | **none** | **75.33** |
| Status | `REJECTED_MISSING_RESULT` | `PARTIAL_RENORMALISED` (available weight 75%) |
| Shown to user | "No combined score: Momentum Analysis returned INSUFFICIENT_DATA (needs 200 bars, 140 available)." | "75.33 — based on 75% of the profile; Momentum Analysis missing (INSUFFICIENT_DATA)." |

Note how option B **raised** the score from 71.50 to 75.33. The missing scanner was the weakest, so leaving it out flattered the result. This is the main risk of option B.

### 5.4 Comparison

| Aspect | A — Reject | B — Renormalise |
|---|---|---|
| Transparency | Complete: a score is always the full profile | Good, if the flag and available weight are always shown |
| Comparability across instruments | High: every score uses the same scanners and weights | Low: two instruments' scores may rest on different scanner sets |
| Risk of misleading results | Low | Moderate: a missing weak (or strong) scanner shifts the score, as in 5.3 |
| Number of instruments with a score | Fewer (any gap removes the score) | More |
| Behaviour with short histories | Many new listings get no score | Scores still produced |
| Simplicity | Simplest | Slightly more logic, plus a minimum-coverage rule |
| Fit with the blueprint ("simple, deterministic, transparent") | Strong | Acceptable with safeguards |

### 5.5 Decision (OD-03 — confirmed: Option A, Reject)

**Confirmed (Owner wording):** *Reject the combined score if a required scanner result is missing or invalid.* Sections 5.1–5.4 are kept as the record of why. The text below was the recommendation before confirmation; the option B safeguards it mentions are **not** part of P1, and option B is not implemented. Reconsidering it would be a new Owner decision.

*Original recommendation, retained for the record:*

**Recommend Option A (Reject) for the first version.**
- It keeps every combined score directly comparable.
- It cannot flatter an instrument by dropping a weak result.
- It makes data gaps visible rather than hiding them inside a number.

The owner might prefer option B, for example for a stock universe where many instruments have short histories. In that case, adopt B **only with these safeguards**:
1. A minimum available weight, recommended **at least 70%**, below which no score is produced.
2. A status of `PARTIAL_RENORMALISED`, with the available weight shown next to every such score in every report.
3. Renormalised scores sorted or flagged separately from full scores in rankings.

The profile field `missing_result_policy` is kept so that each profile states its policy explicitly; in P1 its only valid value is `REJECT` (W-6). `min_available_weight` is not used in P1.

**Edge cases that apply to both options:**
- If **no** scanner has a valid result, there is no combined score; status `NO_VALID_RESULTS`.
- A profile with a single scanner is allowed; its combined score equals that scanner's score.

---

## 6. Combined result structure

```json
{
  "combined_schema_version": "1.0",
  "instrument_id": "CONCOR",
  "profile": {"profile_id": "example_profile", "profile_version": 1,
              "meaning": "...", "missing_result_policy": "REJECT"},
  "status": "COMPLETE",
  "status_messages": [],
  "components": [
    {"scanner_id": "scanner_a", "scanner_version": "1.0.0", "result_status": "OK",
     "score": 80.0, "weight": 40.0, "contribution": 32.0, "used": true},
    {"scanner_id": "scanner_b", "scanner_version": "1.0.0", "result_status": "OK",
     "score": 70.0, "weight": 35.0, "contribution": 24.5, "used": true},
    {"scanner_id": "scanner_c", "scanner_version": "1.0.0", "result_status": "OK",
     "score": 60.0, "weight": 25.0, "contribution": 15.0, "used": true}
  ],
  "available_weight": 100.0,
  "combined_score": 71.5
}
```

| `status` | Meaning |
|---|---|
| `COMPLETE` | All scanners valid |
| `REJECTED_MISSING_RESULT` | Option A applied; `combined_score` is null |
| `PARTIAL_RENORMALISED` | *Not produced in P1* (option B not adopted) |
| `BELOW_MIN_WEIGHT` | *Not produced in P1* (option B not adopted) |
| `NO_VALID_RESULTS` | Nothing to combine |

---

## 7. AI-friendly run output (F-35, P1; F-38 P2)

### 7.1 Principle

The output must be complete and useful **without any AI** (Approved — blueprint). It is also structured so that it can be pasted or attached to Claude or ChatGPT for explanation, which is a manual step outside Q-MAP.

In P1 there is no AI connection, no API key and no automation.

### 7.2 Files produced by every run

| File | Purpose |
|---|---|
| `Q-MAP_Run_<dd_mmm_yy_hhmmss>.json` | Complete machine-readable record of the run |
| `Q-MAP_Run_Report_<dd_mmm_yy_hhmmss>.xlsx` | Readable report. Sheets: Summary, Combined_Scores, Scanner_Results (one row per instrument and scanner), Facts, Data_Warnings, Run_Settings. |

Both are written to the folder the user picks. Dates displayed in the report use dd-mmm-yy. Dates inside the JSON use ISO `YYYY-MM-DD`, the standard machine format, which is explained in the JSON's own notes (7.3).

### 7.3 JSON layout — five clearly separated sections

```json
{
  "qmap_run_output_version": "1.0",
  "schema_notes": {
    "timestamps": "IST (Asia/Kolkata) wall-clock; intraday times are interval START; dates ISO YYYY-MM-DD",
    "sections": "1 run_context, 2 data_references, 3 scanner_results, 4 combined_scores are calculated by Python and are authoritative. 5 interpretation is optional commentary and never changes 1-4.",
    "missing_values": "null means not available; it never means zero",
    "scores": "0-100; meaning defined per scanner (score.calibration) and per profile (profile.meaning)"
  },
  "1_run_context": {
    "run_id": "RUN_11_Nov_26_183427",
    "created_at": "2026-11-11T18:34:27+05:30",
    "qmap_version": "1.0.0",
    "contract_version": "1.0",
    "run_config": {"...": "complete configuration incl. all parameters"}
  },
  "2_data_references": [{"...": "every data request with data_version, warnings, issues"}],
  "3_scanner_results": [{"...": "ScannerResult objects (document 04, section 7.5)"}],
  "4_combined_scores": [{"...": "combined results (section 6)"}],
  "5_interpretation": null,
  "integrity": {
    "content_sha256": "SHA-256 of sections 1-4 serialised in canonical form (sorted keys, no spaces)",
    "note": "Any change to sections 1-4 changes this value."
  }
}
```

**Separation required by the assignment:**

| Required separation | Where |
|---|---|
| Original data references | `2_data_references` |
| Objective facts | `3_scanner_results[*].facts` |
| Individual scanner outputs | `3_scanner_results[*].calculations`, `.score` |
| Combined score and contributions | `4_combined_scores` |
| Optional AI interpretation | `5_interpretation` (always `null` from Python) and the separate interpretation file (7.4) |

### 7.4 Optional interpretation layer (F-38 — P2, Deferred; structure reserved now)

If interpretation is later added, it is stored in a **separate file**: `Q-MAP_Run_<suffix>_interpretation.json`.

```json
{
  "interprets_run_file": "Q-MAP_Run_11_Nov_26_183427.json",
  "run_content_sha256": "<copied from the run file>",
  "author": "Human / name of AI assistant",
  "created_at": "...",
  "commentary": "...",
  "statement": "Commentary only. It does not change any data, calculation, score or weight in the run file."
}
```

The run file itself is never edited after it is written. If a reader finds that the hash in an interpretation does not match the run file, that interpretation does not belong to that run. This makes it impossible for commentary to alter, or masquerade as, the calculated results.

---

## 8. Features and priorities in this document

| Feature | Priority | Complexity | Status |
|---|---|---|---|
| F-34 Weighted combined score with validation, policy and full transparency | P1 | Moderate | Proposed design; OD-02 meaning and OD-03 reject policy **confirmed**; profile composition and weights pending (G-10) |
| Per-scanner calibration rules CAL-1 to CAL-7 | P1 | Moderate (per scanner) | Proposed; each calibration OD-09 |
| F-35 Run JSON with integrity hash | P1 | Low | Proposed |
| F-36 Excel run report | P1 | Low | Proposed |
| F-38 Interpretation file and verifier | P2 | Low | Deferred (structure reserved) |
| F-39 Direct AI integration | P3 | High | Deferred |
| Frozen reference-percentile calibration | P2 | Moderate | Deferred |

*End of document 05, v1.1.*
