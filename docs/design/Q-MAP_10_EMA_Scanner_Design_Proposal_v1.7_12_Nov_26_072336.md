# Q-MAP — EMA Scanner Design Proposal

**Supplementary document 10 | Version 1.7 | 12-Nov-26 | Status: METHODOLOGY APPROVED — D-EMA-01 to D-EMA-10 approved by the Project Owner on 11-Nov-26, subject to G-03; combined-score weight deferred (G-10). D-EMA-11 and D-EMA-12 are **proposals**. All CONCOR and INFY reference values verified against source data (document 13 v1.2). Not approval to code.**

| Field | Value |
|---|---|
| Responds to | Additional Groundwork Assignment, Task 2 |
| Follows | Scanner specification template (document 04 v1.2 §8); scanner contract (04 v1.2 §7); calibration rules CAL-1 to CAL-7 (05 v1.1 §3); data-access interface 1.1 (03 v1.2); decisions consolidated in document 12; OD-01 (EMA Analysis on daily stocks as first-scanner candidate); OD-09 (fixed-anchor or rule-based calibration) |
| Prepared by | Claude 2 |

> This package is a design and preparation deliverable. It is not approval to begin production coding.
>
> **Approval status (v1.4).** The methodology in this document — data, periods, the six comparisons, slope check, state bands, score formula, exact comparison, 800-bar window, continuity handling and combined-score eligibility (D-EMA-01 to D-EMA-10) — was **approved by the Project Owner on 11-Nov-26**, subject to G-03. Sections previously marked [PROPOSED] are now marked [APPROVED]. The **only** open item in this document is the stale-data rule **D-EMA-11**, still marked [PROPOSED]. The combined-score weight is not set here (G-10). No scanner code has been written.
>
> **Verification status (v1.6).** Document 13 v1.1 records the check of every example. **The CONCOR reference values (T-EMA-01, 02, 05, 06, 07, 08, 09, 18) have been verified against the CONCOR source file**; one date was corrected (T-EMA-09). **The INFY values (T-EMA-03, 04) have been verified against the INFY source file** (document 13 v1.2): exact to 4 dp, with no ±15% move in either window, so both are valid `OK` results. The fixtures were recomputed in full. Two implementation-precision findings (EMA-F1: floating-point drift breaks exact ties, e.g. T-EMA-10; EMA-F2: the stored score depends on formula order) are recorded with a proposed rule, **D-EMA-12**, for the Owner's decision. They do not change the approved methodology.
>
> The reference values were produced by an exploratory calculation during this design work, **not** by Q-MAP code. **No independent verification of them (in Excel or otherwise) has been performed by anyone.** Claude 2 has re-checked only the arithmetic that follows from the written values (see §B9). They must be reproduced independently (Part B §B9.2) before M3.

**Change log**

| Version | Changed sections | Reason |
|---|---|---|
| 1.0 | — | First issue |
| 1.1 | New §A1a | Distinguishes trend alignment, Combined Technical Setup Strength (OD-02, approved) and probability of profit |
| 1.1 | §A6 | 800 bars explained as a stability and warm-up **policy**, not a mathematical minimum; the consequence for stocks with 200–799 bars shown; relation to the confirmed OD-07 |
| 1.1 | §A7, §B9.3 | Dependence of every example and test on gap G-03 stated explicitly |
| 1.1 | §A10 | D-EMA-08 alternatives expanded with evidence; **D-EMA-10 rewritten** so that it does not redefine OD-02 |
| 1.1 | §B4 | Warm-up evidence table added |
| 1.2 | §A4, §A5, §A7 (INFY wording), §A8, §A10 (D-EMA-05), §B4, §B10, §B9.3 (new T-EMA-16) | **Classification corrected to cover every possible net count from −6 to +6.** An exact tie scores 0, so odd net counts (±1, ±3, ±5) are possible. There are up to **13** score levels, not seven. ±3 are now labelled "neutral, leaning bullish/bearish". The six-question method (+1, −1, 0) is unchanged. |
| 1.3 | §A4 | "Six yes/no questions" corrected to "six comparison questions": an exact tie is a third answer (0) |
| 1.3 | §A6 | Effect of the 800-bar policy on short-history stocks stated more fully; universe-wide effect unknown until the inventory |
| 1.3 | §A7, §B9.3 | G-03 dependencies re-checked against the recommended close-based continuity rule (document 12); a further dependency found for open-only anomalies (new T-EMA-18) |
| 1.3 | §A10 | New proposed decision **D-EMA-11** (stale data: requested analysis date later than the stock's last trading day). Decisions consolidated in document 12. |
| 1.3 | §B2 | Requirement now carries `latest_n` (interface 1.1, document 03 v1.2); continuity blocking follows SC-07 (`affects_continuity` only); stale-data rule added as a proposal |
| 1.3 | §B9 | Test status stated: all T-EMA tests are **specified, not executed**; T-EMA-17 and T-EMA-18 added |
| 1.4 | Header, §A3–§A6, §A9, §A10, §B1, §B3 | D-EMA-01 to D-EMA-10 recorded as **approved** (Owner, 11-Nov-26); [APPROVED] → [APPROVED]; D-EMA-11 stays a proposal; combined weight deferred |
| 1.4 | §A7, §B2, §B9.3, §B10 | G-03 as approved: every ±15% move — open or close — blocks until the Owner verifies it. Expected results restated: CONCOR examples are `INVALID_DATA` until 04-Jun-24 is verified; T-EMA-18 is `INVALID_DATA` until 15-May-06 is verified. |
| 1.4 | Header note, §B9 | Arithmetic re-checks clearly separated from independent verification, which has not been done |
| 1.5 | Header; notice below; T-EMA-10; §B8 note | Final verification (document 13): arithmetic of all examples confirmed; source verification not possible (files not supplied); two implementation-precision findings recorded (EMA-F1, EMA-F2) with proposal D-EMA-12. **Methodology unchanged.** |
| 1.6 | Header; verification notice; §A7 CONCOR note; T-EMA-09; T-EMA-18; note after §B9.3 table | CONCOR examples verified against the source file (document 13 v1.1). T-EMA-09: the 08-Dec-16 window starts **10-Sep-13**, not 09-Sep-13. T-EMA-18: values calculated and labelled **conditional** on G-03 verification. Three newly identified CONCOR G-03 cases and their effect on CONCOR's history recorded. **Methodology unchanged.** |
| 1.7 | Header; verification notice; §A7 INFY rows and note; T-EMA-03, T-EMA-04, T-EMA-07 | INFY examples verified against the INFY source file (exact; no ±15% move in either window); INFY's ±15% history (seven newly identified G-03 cases) noted. **Methodology unchanged.** |

**Review result (v1.3).** Checked against OD-01, OD-07, OD-09, the data-quality design, the scanner interface, combined scoring and the testing strategy. The scoring method, parameters and examples are **unchanged**. The score formula and all 13 score/state mappings were recomputed and agree with §A5 and T-EMA-16. The six answers and net counts of the four worked examples were recomputed from their listed EMA values and agree. The EMA values themselves come from the earlier exploratory calculation on the source files, which are not in this workspace; they still need the independent Excel reproduction of §B9.2.

**What "re-checked" means (v1.4).** Claude 2 recomputed (a) the score formula and its 13 mappings, (b) the six answers and net counts of the four examples **from the EMA values written in this document**, (c) the T-EMA-01 arithmetic and (d) the distances in §B8. This proves internal arithmetic consistency only. It does **not** prove that the written closes and EMA values match the source data; that requires the independent reproduction of §B9.2, which has not yet been performed.

All EMA periods, rules and thresholds remain **proposals**. No approved Owner decision is reopened.

---

# Part A — Plain-language summary for the Project Owner

## A1. What the scanner is meant to identify

For one stock, on one chosen date, the scanner answers:

> **"Based on its daily closing prices, is this stock's trend currently up, down, or unclear — and how consistently?"**

It does this by comparing the latest closing price with three smoothed price lines (EMAs), and the lines with each other. It does **not** predict prices, give buy or sell advice, or use volume. It describes the present trend in a consistent, checkable way.

## A1a. Three different things — and which one this scanner measures

| Concept | What it is | Status |
|---|---|---|
| **Trend alignment** (this scanner) | How consistently a stock's closing price and its 20/50/200-day EMAs point in one direction **today**. Expressed as the EMA scanner's own 0–100 score. | **Proposed** (this document) |
| **Combined Technical Setup Strength** | How strongly a stock satisfies the technical conditions measured by the **selected scanners** taken together. It is the meaning of the combined score. | **Approved (OD-02).** Not redefined here. |
| **Probability of profit** | The chance that a trade makes money | **Not measured by Q-MAP.** Neither the EMA score nor the combined score is a probability, a forecast or advice. A score of 100 does not mean "certain to rise". |

The EMA scanner contributes **one** measure, trend alignment, which a scoring profile may use as one input to Combined Technical Setup Strength (§A10, D-EMA-10).

## A2. What an EMA is, in one paragraph

An **Exponential Moving Average (EMA)** is a smoothed version of the closing price. Each day it moves a fixed fraction of the way towards that day's close. A **short** EMA (e.g. 20 days) follows price closely; a **long** EMA (e.g. 200 days) moves slowly and shows the long-term direction. When price is above its EMAs, and the short EMAs are above the long ones, the stock is in an orderly up-trend. The reverse is an orderly down-trend. A mixture means the trend is unclear.

## A3. Which EMA periods, and why [APPROVED]

| Line | Period | Represents | Why this period |
|---|---|---|---|
| Short | **20 trading days** (about 1 month) | Recent direction | Widely used; responsive without being noisy |
| Medium | **50 trading days** (about 2½ months) | Intermediate trend | Common "intermediate trend" reference |
| Long | **200 trading days** (about 10 months) | Long-term trend | The most widely watched long-term trend line |

Using common periods means the results can be compared with what you see on any charting platform, which makes them easier to verify and trust. Alternatives are in §A8.

## A4. How bullish, bearish and neutral are decided [APPROVED]

The scanner asks **six comparison questions** about the chosen date. Each has three possible answers: above (bullish, +1), below (bearish, −1) or exactly equal (0):

| # | Question | "Above" (+1) is a bullish sign |
|---|---|---|
| 1 | Is the close above the 20-day EMA? | Price above its short trend |
| 2 | Is the close above the 50-day EMA? | Price above its intermediate trend |
| 3 | Is the close above the 200-day EMA? | Price above its long-term trend |
| 4 | Is the 20-day EMA above the 50-day EMA? | Short trend leading the intermediate trend |
| 5 | Is the 50-day EMA above the 200-day EMA? | Intermediate trend above the long-term trend |
| 6 | Is the 50-day EMA higher than it was 10 trading days ago? | The intermediate trend is rising |

Each "yes" counts **+1**, each "no" counts **−1**, and an exact tie counts **0**. The six answers are added to give a **net count** between −6 and +6.

| Net count | State |
|---|---|
| +4 to +6 | **BULLISH** |
| +3 | **NEUTRAL, LEANING BULLISH** |
| −2 to +2 | **NEUTRAL** (mixed signals) |
| −3 | **NEUTRAL, LEANING BEARISH** |
| −6 to −4 | **BEARISH** |

Every whole number from −6 to +6 falls into exactly one band. **Odd net counts (±1, ±3, ±5) occur only when at least one answer is an exact tie (0).** Six answers of +1 or −1 always add up to an even number. With exact comparison (D-EMA-07 at 0%), ties are rare; with a near-the-line allowance they become more frequent.

## A5. The score and how to read it [APPROVED]

**Score = 50 + 50 × (net count ÷ 6)**, which always lies between 0 and 100.

| Score | Net count | State | Meaning |
|---:|---:|---|---|
| **100** | +6 | Bullish | Every sign bullish: orderly up-trend |
| 91.67 | +5 | Bullish | Five bullish signs, one exact tie |
| 83.33 | +4 | Bullish | Mostly bullish |
| 75 | +3 | Neutral, leaning bullish | Bullish signs outweigh bearish ones, with at least one tie |
| 66.67 | +2 | Neutral | Mixed, tilted bullish |
| 58.33 | +1 | Neutral | Mixed, slightly bullish (needs a tie) |
| **50** | 0 | Neutral | Evenly mixed, no trend |
| 41.67 | −1 | Neutral | Mixed, slightly bearish (needs a tie) |
| 33.33 | −2 | Neutral | Mixed, tilted bearish |
| 25 | −3 | Neutral, leaning bearish | Bearish signs outweigh bullish ones, with at least one tie |
| 16.67 | −4 | Bearish | Mostly bearish |
| 8.33 | −5 | Bearish | Five bearish signs, one exact tie |
| **0** | −6 | Bearish | Every sign bearish: orderly down-trend |

A higher score means a **more consistently bullish trend**. This follows the direction rule for combined scoring (CAL-3). The score uses fixed rules only, so the same data always gives the same score, which makes it rule-based calibration under OD-09.

Note that the score moves in **steps of 8.33**, so it can take **up to 13 values**. The seven even net counts are the common case; the six odd ones need at least one exact tie. This coarseness is deliberate: it is easy to check by hand. The trade-off is that it cannot show how *far* price is from its lines. §A8 explains this.

## A6. How much history is needed, and what happens when there is not enough [APPROVED]

**What is mathematically required, and what is proposed.** An EMA200 *can* be calculated as soon as 200 daily closes exist: the first value is the average of those 200 closes. That first value, however, is dominated by its starting point. Every later value still carries a share of that starting average, which shrinks only gradually:

| Daily bars used | Share of the EMA200 still coming from its starting average |
|---:|---:|
| 200 (minimum possible) | 100% |
| 400 | 13.5% |
| 600 | 1.8% |
| **800 (proposed)** | **0.25%** |
| 1,000 | 0.03% |

The proposed **800-bar rule is therefore a stability and warm-up policy, not a mathematical minimum.** It ensures that the EMA200 depends on recent prices rather than on where the calculation happened to start, and that a value computed by Q-MAP matches a long-history chart closely. On CONCOR at 06-Nov-26, the 800-bar EMA200 differs from a full-history EMA200 by 0.012%; a 200-bar EMA200 differs by 0.77%.

**Practical consequence (to be weighed before approval).** Under the proposed rule:
- A stock with **fewer than 800 complete daily bars** (about 3¼ years) receives **no EMA score**. Its result is "insufficient data", with the actual number of bars disclosed.
- This includes stocks with **200–799 bars**, for which an EMA200 could be calculated mathematically but is not yet considered stable.
- Recently listed stocks will therefore be excluded from this scanner for their first three years or so.
- *Example:* CONCOR on 31-Dec-01 had 690 bars, so the result is insufficient data. Its first scoreable date is 06-Jun-02.

**What this means for stocks without enough history (v1.3).** Such a stock is not hidden and not given a guessed number. Its result is `INSUFFICIENT_DATA`, showing the bars it has and the 800 it needs, so it appears in the output as "not scoreable yet". Because OD-03 rejects a combined score when a required result is missing, the same stock also gets **no combined score** in any profile that includes the EMA scanner. How many stocks this affects is **unknown** until the universe inventory reports row counts per file (document 09 v1.3 §8, item U-05); in the inspected files, all three daily instruments have more than 800 bars.

**Relation to the confirmed OD-07** (use available history, disclose actual coverage, report calculations as unavailable when history is insufficient):
- The scanner always discloses the bars available and the bars required.
- It reports "unavailable" rather than a guessed or unstable value.
- What counts as "insufficient" for this scanner is the threshold chosen in D-EMA-08. That threshold is the Owner's choice; §A10 shows lower alternatives and their trade-off.

**Breaks in the price series.** If the 800-day window contains a known, unverified break that is marked as affecting continuity, the scanner reports "invalid data" and gives no score.
- *Example:* CONCOR's unverified −36.5% gap on 06-Sep-13. Every analysis date from 06-Sep-13 to 07-Dec-16 is invalid; the first valid date after it is 08-Dec-16.
- Under the approved G-03 rule, every ±15% move (open or close) affects continuity until the Owner verifies it.

## A7. Real examples (actual data, ending 06-Nov-26 unless stated)

| Stock and date | Close | EMA 20 | EMA 50 | EMA 200 | Six answers | Net | Score | State | Status under the approved G-03 rule |
|---|---:|---:|---:|---:|---|---:|---:|---|---|
| **CONCOR, 06-Nov-26** | 439.80 | 432.73 | 452.66 | 486.45 | ✓ ✗ ✗ ✗ ✗ ✗ | −4 | **16.67** | **BEARISH** | Window contains 04-Jun-24 (−19.2%): **`INVALID_DATA` by default**; the values shown apply once the Owner marks 04-Jun-24 `VERIFIED_OK` |
| **INFY, 06-Nov-26** | 1,181.40 | 1,132.26 | 1,108.54 | 1,203.88 | ✓ ✓ ✗ ✓ ✗ ✓ | +2 | **66.67** | **NEUTRAL** | `OK` — no move beyond ±15% in the window (source-verified, document 13) |
| **INFY, 03-Feb-26** | 1,656.00 | 1,646.10 | 1,617.61 | 1,589.18 | ✓ ✓ ✓ ✓ ✓ ✓ | +6 | **100** | **BULLISH** | `OK` — window 16-Nov-22 to 03-Feb-26 has no move beyond ±15% (source-verified, document 13) |
| **CONCOR, 09-Sep-26** | 510.00 | 509.89 | 504.10 | 506.02 | ✓ ✓ ✓ ✓ ✗ ✓ | +4 | **83.33** | **BULLISH** | Window contains 04-Jun-24: **`INVALID_DATA` by default**; values apply once 04-Jun-24 is `VERIFIED_OK` |

**In plain words:**
- **CONCOR now:** price has just moved above its 20-day line, but it is below the 50- and 200-day lines, the lines are stacked downwards, and the 50-day line is falling. A down-trend with a small short-term bounce.
- **INFY now:** price and the short lines are rising and above the 50-day line, but still below the 200-day line, which is above the 50-day. A recovery that has not yet turned the long-term trend. Net +2, so the scanner calls it **neutral** (score 66.67, on the bullish side of 50, but short of the +3 needed for "neutral, leaning bullish").
- **INFY in early February:** everything aligned upwards, a textbook up-trend.
- **CONCOR on 09-Sep-26:** labelled bullish, even though the 50-day line was still slightly **below** the 200-day line, and price was only 0.02% above its 20-day line. This shows a real limitation: a tiny price change can flip an answer. See the decisions on "near-the-line" handling (§A10, D-EMA-07) and on a stricter bullish rule (D-EMA-05).

**About the two CONCOR examples (restated in v1.4).** Both 800-day windows include **04-Jun-24**, when CONCOR closed −19.2%. That move is plausibly genuine (2024 election-result day) but unverified. Under the Owner's approved G-03 rule, **both CONCOR examples are `INVALID_DATA` until the Owner verifies 04-Jun-24 and marks it `VERIFIED_OK`**; the values in the table are what the scanner produces after that. The INFY examples are unaffected.

*CONCOR's full ±15% history (v1.6).* The source check (document 13 §4) found three further G-03 cases besides those listed above: 31-Jan-08 (close +15.83%), 20-Mar-20 (close +16.09%) and 10-Aug-20 (close −15.24%). Each blocks until the Owner verifies it; none is classified, quarantined or unblocked. None lies in the windows of the examples above (they start 17-Aug-23 and 21-Jun-23). Until any occurrence is verified, CONCOR has an EMA result only for analysis dates 06-Jun-02 – 25-May-04, 04-May-11 – 05-Sep-13, 08-Dec-16 – 19-Mar-20 and 30-Oct-23 – 03-Jun-24.

*INFY's full ±15% history (v1.7).* The INFY source check (document 13 v1.2 §6) found seven G-03 cases besides 24-Oct-03: 08-Aug-00 (close +15.85%), 11-Apr-01 (−16.01%), 18-Apr-01 (+16.00%), 10-Apr-03 (−26.56%), 11-Jan-13 (+16.78%), 12-Apr-13 (−21.26%) and 22-Oct-19 (−16.19%). Each blocks until the Owner verifies it; none is classified, quarantined or unblocked. None lies in the windows of the INFY examples. Until any occurrence is verified, INFY has an EMA result only for analysis dates 28-Dec-06 – 10-Jan-13, 13-Jul-16 – 18-Oct-19 and 06-Jan-23 – 06-Nov-26.

*Open-price-only anomalies (v1.4).* Under the approved G-03 rule, moves in the **open** only also block, although their closes moved only +3.1% (CONCOR 26-May-04), +0.3% (27-May-04), −3.6% (15-May-06) and +3.1% (INFY 24-Oct-03). Until the Owner verifies each, CONCOR has no EMA score for analysis dates from 26-May-04 until about 800 trading days after 15-May-06, and INFY none for about 800 trading days after 24-Oct-03. This affects historical analysis only, not current results. A proposal to treat open-only moves differently for close-based scanners is recorded separately as **P-01** in document 12; it is **not** part of this approved design. Test T-EMA-18 covers the approved behaviour.

## A8. Alternatives in brief

| Approach | What it measures | For | Against |
|---|---|---|---|
| **1. Six-question alignment count (recommended)** | Consistency of trend signals | Simple, explainable, checkable by hand; matches "rule-based" calibration (OD-09) | Only up to 13 coarse score levels; ignores distance from the lines; sensitive right at a line |
| 2. Distance-based score | How far price is above or below the 200-day EMA (e.g. −20% → 0, +20% → 100) | Smooth scores; shows strength | Anchors are arbitrary; volatile stocks hit 0 or 100 constantly; harder to explain |
| 3. Crossover events | Recent "golden" or "death" crosses (50 over or under 200) | Familiar to traders | Rare events; most days have no signal; lags badly |
| 4. Alignment count plus a distance component | A blend of 1 and 2 | Finer scores | More parameters to approve and verify; harder to explain |
| 5. Different periods (e.g. 9/21/50, or 10/30/100) | Faster or slower trend view | Faster reaction | Less standard; harder to compare with charts |

## A9. Recommendation (approved 11-Nov-26)

Adopt **approach 1** with periods **20/50/200**, a **10-day slope check** on the 50-day EMA, and the **800-day fixed window**. Start without a near-the-line allowance, and revisit after the pilot. *The Owner approved this on 11-Nov-26 (D-EMA-01 to D-EMA-10).*

It is the simplest design that is still useful. Anyone can verify it in Excel. It fits the approved rule-based calibration direction, and it proves the whole Q-MAP chain early, as OD-01 intends. Approach 4 can be considered later, once there is experience with approach 1.

## A10. Decisions requested from the Project Owner

**Decision status (v1.4).** D-EMA-01 to D-EMA-10 — **approved by the Owner on 11-Nov-26 as proposed below**, subject to G-03; for D-EMA-10 the weight is deferred to the scoring profile (G-10). D-EMA-11 — **open proposal** (document 12).

| ID | Decision | Proposed | Alternatives |
|---|---|---|---|
| **D-EMA-01** | Data and timeframe | Daily closes of NSE stocks (`NSE_EQ_DAILY`, `1D`) | Also indices; also intraday (later) |
| **D-EMA-02** | EMA periods | 20, 50, 200 | 9/21/50; 10/30/100; Fibonacci set |
| **D-EMA-03** | The six questions | As in §A4 | Fewer (e.g. drop question 6) or additional (e.g. 20-day slope) |
| **D-EMA-04** | Slope check | 50-day EMA versus 10 trading days earlier | 5 or 20 days; use the 20-day EMA instead |
| **D-EMA-05** | State bands | Bullish +4 to +6; Neutral, leaning bullish +3; Neutral −2 to +2; Neutral, leaning bearish −3; Bearish −6 to −4 (covers all net counts −6 to +6) | Stricter: bullish only if questions 3 and 5 are both "yes" |
| **D-EMA-06** | Score formula | 50 + 50 × net ÷ 6 | Weighted questions (e.g. long-term questions count double) |
| **D-EMA-07** | Near-the-line allowance | None in version 1 (exact comparison; an exact tie counts 0) | Treat values within ±0.1% of a line as 0 |
| **D-EMA-08** | History window: stability and warm-up policy | Fixed 800 trading days ending on the analysis date; fewer → “insufficient data” with coverage disclosed (stocks with 200–799 bars receive no score) | **600** bars (1.8% residual starting influence; about 2⅓ years of history); **400** bars (13.5%; about 1½ years); **200** bars (mathematical minimum; unstable); full available history (no fixed window; results then depend on where history starts) |
| **D-EMA-09** | Breaks in the window | Any continuity-affecting open issue in the window → invalid data | Shorten the window to after the break (needs 800 days after it anyway) |
| **D-EMA-10** | Use within combined scoring | The EMA scanner produces **its own trend-alignment score**. It **does not redefine** the approved combined-score meaning (OD-02: Combined Technical Setup Strength). It may be included as one input in a scoring profile **if** that profile's approved composition treats bullish trend alignment as one of the technical conditions it measures. Its weight is set in the profile. | Not included in any profile until a second scanner exists (the M5 timing in any case) |
| **D-EMA-11** *(new in v1.3)* | Stale data: the stock's last stored trading day is earlier than the last trading day on or before the requested analysis date (signalled by `RANGE_TRUNCATED_END`, document 03 v1.2 §A6) | `INSUFFICIENT_DATA` with the message "data ends dd-mmm-yy; analysis date dd-mmm-yy" — no score | Calculate as of the last available date, status `OK`, with the actual date in `facts.analysis_date` and a message |

---

# Part B — Technical specification (follows the template in 04 v1.1 §8)

## B1. Identity [APPROVED]

| Field | Value |
|---|---|
| `scanner_id` | `ema_trend_alignment` |
| `name` | EMA Trend Alignment |
| `version` | 1.0.0 (on approval) |
| `spec_reference` | `docs/scanners/ema_trend_alignment_spec_v1.0.md` (to be created from this proposal on approval) |
| `timeframes` | `("1D",)` |
| `produces_score` | True |
| `score_meaning` | "Consistency of bullish daily EMA trend alignment: 0 = all six signals bearish, 50 = evenly mixed, 100 = all six bullish" |

## B2. Data requirements

```text
DataRequirement(
    instrument_id = <stock>,
    timeframe     = "1D",
    end           = analysis_end,          # the analysis date
    start         = None,
    latest_n      = window_bars,           # interface 1.1 (document 03 v1.2)
    required_fields = ("close",),
    optional_fields = (),
    min_bars      = window_bars,           # 800 by default
    require_complete_bars = True,
    exclude_flagged = False)
```

The scanner calls `context.fetch(requirement)` with this requirement (which carries `latest_n = window_bars` and `end = analysis_end`), then applies these policies:

| Condition in the `BarResult` | Scanner behaviour |
|---|---|
| Fewer than `window_bars` bars returned with `is_complete = True` | `INSUFFICIENT_DATA` ("needs 800 complete daily bars; N available") |
| A forming last bar | Excluded. The window ends on the last complete bar; its date is recorded as the effective analysis date. |
| An issue with `affects_continuity = True` whose dates overlap the window | `INVALID_DATA`, naming the issue (rule SC-07; `affects_continuity` alone decides, and marking an issue `VERIFIED_OK` clears it — document 02 v1.2 §5.2) |
| `RANGE_TRUNCATED_END` (stale data) | **[PROPOSED, D-EMA-11]** `INSUFFICIENT_DATA` with both dates in the message; no score |
| `FLAGGED_ROWS_INCLUDED` (e.g. `LARGE_GAP_UNVERIFIED` without the continuity attribute) | Calculation proceeds; flags listed in `status_messages` |
| `HELD_REVISION_EXISTS` | Calculation proceeds on the active data; warning recorded in `status_messages` |
| Missing days inside the window (`MISSING_DAY` issues) | Calculation proceeds on the bars present (an EMA runs over trading bars); the count is recorded in `status_messages` |
| Volume warnings | Ignored (volume not used) |

Only the `close` is used. The open-only anomalies in Deliverable 1 (CONCOR 2004/2006, INFY 2003) therefore do not affect this scanner.

## B3. Parameters [APPROVED defaults]

| Name | Meaning | Default | Allowed |
|---|---|---|---|
| `short_period` | Short EMA length (bars) | 20 | Integer 2–100, < `medium_period` |
| `medium_period` | Medium EMA length | 50 | Integer > `short_period`, < `long_period` |
| `long_period` | Long EMA length | 200 | Integer ≤ 400 |
| `slope_lookback` | Bars back for question 6 | 10 | Integer 1–50 |
| `window_bars` | Fixed calculation window | 800 | Integer ≥ 4 × `long_period` |
| `tie_band_pct` | Near-the-line allowance (D-EMA-07) | 0.0 | 0.0–1.0 |

## B4. Calculations

Let the window contain closes `c[0] … c[W−1]`, oldest first, with `W = window_bars`. The last bar `W−1` is the analysis bar.

**EMA definition (one period N):**
- smoothing factor `α = 2 ÷ (N + 1)`
- seed: `EMA[N−1] = arithmetic mean of c[0] … c[N−1]` (simple-average seed at the start of the window)
- recursion, for `i = N … W−1`: `EMA[i] = α × c[i] + (1 − α) × EMA[i−1]`
- EMA values before index `N−1` are undefined and never used.

All three EMAs are computed independently over the **same** window, each with its own seed.

**Warm-up evidence (D-EMA-08).** Remaining weight of the starting average in EMA200 = (1 − 2/201)^(bars − 200): 100% at 200 bars, 13.5% at 400, 1.8% at 600, 0.25% at 800, 0.03% at 1,000. Measured on CONCOR (06-Nov-26), the difference from a full-history EMA200 is: 200 bars −0.77%; 400 bars +0.007%; 600 bars +0.17%; 800 bars −0.012%. The individual differences depend on the price path, so the residual-weight column is the general guide.

**Why a fixed window with a simple-average seed (D-EMA-08):**
- An EMA strictly depends on where its calculation starts. Computing from a stock's first-ever bar would make results change whenever earlier history is added or revised, and would mean thousands of rows to verify.
- A fixed 800-bar window makes each result depend only on those 800 closes, which is reproducible and verifiable in one Excel sheet.
- The cost is a tiny difference from full-history values. Measured on CONCOR at 06-Nov-26 (exploratory check):

| EMA | Window 4N, average seed | Full history | Difference |
|---|---:|---:|---:|
| 20 (window 80) | 432.7317 | 432.7297 | 0.0005% |
| 50 (window 200) | 452.6772 | 452.6585 | 0.004% |
| 200 (window 800) | 486.4492 | 486.5087 | 0.012% |

(Within the proposed 800-bar window, EMA20 and EMA50 have even longer warm-ups and match full history to four decimals: 432.7297 and 452.6585.)

**Questions.** Write `sgn(x) = +1` if `x > t`, `−1` if `x < −t`, else `0`. Here `t = 0` when `tie_band_pct = 0`; otherwise `t = tie_band_pct ÷ 100 × reference value`, where the reference value is the EMA being compared against. Let `s = short_period`, `m = medium_period`, `L = long_period`, `k = slope_lookback`.

| # | Expression |
|---|---|
| Q1 | `sgn(c[W−1] − EMA_s[W−1])` |
| Q2 | `sgn(c[W−1] − EMA_m[W−1])` |
| Q3 | `sgn(c[W−1] − EMA_L[W−1])` |
| Q4 | `sgn(EMA_s[W−1] − EMA_m[W−1])` |
| Q5 | `sgn(EMA_m[W−1] − EMA_L[W−1])` |
| Q6 | `sgn(EMA_m[W−1] − EMA_m[W−1−k])` |

**Net, score and state:**
- `net = Q1 + … + Q6`
- `score = 50 + 50 × net ÷ 6` (full precision stored; displayed to 2 decimals, rounding half up)
- `state` (covers every integer net from −6 to +6):
  - `net ≥ 4` → `BULLISH`
  - `net = 3` → `NEUTRAL_LEANING_BULLISH`
  - `−2 ≤ net ≤ 2` → `NEUTRAL`
  - `net = −3` → `NEUTRAL_LEANING_BEARISH`
  - `net ≤ −4` → `BEARISH`
- Possible scores: 50 + 50 × net ÷ 6 for net = −6 … +6, i.e. 0, 8.33, 16.67, 25, 33.33, 41.67, 50, 58.33, 66.67, 75, 83.33, 91.67, 100 (13 levels; odd nets need at least one tie)

**Precision.** Double-precision arithmetic throughout. Comparisons use the full-precision values, never rounded ones.

## B5. Outputs

| Section | Item | Unit |
|---|---|---|
| `facts` | `analysis_date`, `window_start_date`, `window_bars`, `close` | date, date, count, ₹ |
| `facts` | `ema_short`, `ema_medium`, `ema_long`, `ema_medium_lookback` | ₹ |
| `calculations` | `distance_to_short_pct`, `distance_to_medium_pct`, `distance_to_long_pct` (`(close ÷ EMA − 1) × 100`) | % (informational; not used in the score) |
| `calculations` | `answers` (Q1–Q6 as +1, 0 or −1, with names), `net`, `state` | — |
| `score` | `value`, `scale` "0-100", `calibration` "rule-based alignment count v1 (D-EMA-06)", `components` = the six answers, each weighted 1/6 | — |
| `detail_tables` (optional) | The 800-row table of date, close, EMA20, EMA50, EMA200 | For verification |

## B6. Calibration compliance (05 v1.0 §3.1)

| Rule | How it is met |
|---|---|
| CAL-1 Defined and versioned | §B4; calibration v1 |
| CAL-2 Meaning of 0, 50, 100 | §A5 |
| CAL-3 Direction | Higher = more bullish |
| CAL-4 Deterministic, fixed | Fixed rules; fixed window |
| CAL-5 Clipped | Mathematically confined to 0–100 |
| CAL-6 Independent of the run universe | Uses only this stock's closes |
| CAL-7 Hand-verified examples | §B9 |

## B7. Status rules

| Status | When |
|---|---|
| `OK` | 800 complete bars, no blocking continuity issue |
| `INSUFFICIENT_DATA` | Fewer than `window_bars` complete bars ending at the analysis date |
| `INVALID_DATA` | A blocking continuity issue overlaps the window |
| `NOT_APPLICABLE` | The instrument is not in a daily dataset |
| `ERROR` | Unexpected failure (handled by the runner) |

## B8. Example result (CONCOR, 06-Nov-26; abbreviated)

```json
{
  "scanner": {"scanner_id": "ema_trend_alignment", "version": "1.0.0"},
  "subject": {"instrument_id": "CONCOR", "timeframe": "1D", "analysis_end": "2026-11-06"},
  "parameters": {"short_period": 20, "medium_period": 50, "long_period": 200,
                 "slope_lookback": 10, "window_bars": 800, "tie_band_pct": 0.0},
  "status": "OK",
  "facts": {"analysis_date": "2026-11-06", "window_start_date": "2023-08-17", "window_bars": 800,
            "close": 439.80, "ema_short": 432.7297, "ema_medium": 452.6585,
            "ema_long": 486.4492, "ema_medium_lookback": 466.7276},
  "calculations": {"distance_to_short_pct": 1.6339, "distance_to_medium_pct": -2.8407,
                   "distance_to_long_pct": -9.5897,
                   "answers": {"Q1": 1, "Q2": -1, "Q3": -1, "Q4": -1, "Q5": -1, "Q6": -1},
                   "net": -4, "state": "BEARISH"},
  "score": {"value": 16.666666666666668, "scale": "0-100",
            "calibration": "rule-based alignment count v1"},
  "interpretation": null
}
```

EMA values are shown to 4 decimals here; the stored values have full precision. *Note (v1.5):* the score `16.666666666666668` shown above is one of three different floating-point results that equivalent forms of the formula give (`16.666666666666664`, `16.66666666666667`, `16.666666666666668`); proposal D-EMA-12 fixes the stored score at 2 decimal places (16.67), matching T-EMA-16 (document 13, EMA-F2).

## B9. Independently verifiable examples and test cases

### B9.1 Small EMA arithmetic check (manually verifiable)

EMA with N = 3 (α = 0.5) on CONCOR's last six closes:

| Date | Close | EMA(3) | Working |
|---|---:|---:|---|
| 30-Oct-26 | 413.85 | — | |
| 02-Nov-26 | 417.85 | — | |
| 03-Nov-26 | 419.15 | **416.95** | seed = (413.85 + 417.85 + 419.15) ÷ 3 = 1,250.85 ÷ 3 |
| 04-Nov-26 | 425.10 | **421.025** | 0.5 × 425.10 + 0.5 × 416.95 |
| 05-Nov-26 | 440.85 | **430.9375** | 0.5 × 440.85 + 0.5 × 421.025 |
| 06-Nov-26 | 439.80 | **435.36875** | 0.5 × 439.80 + 0.5 × 430.9375 |

### B9.2 Excel verification method for the full examples

1. Use the data-access interface to retrieve the 800 closes (or copy them from the source file), for example CONCOR from 17-Aug-23 to 06-Nov-26.
2. Put the closes in column B, rows 2–801.
3. EMA200 in column C:
   - `C201 = AVERAGE(B2:B201)`
   - `C202 = 2/201*B202 + (1-2/201)*C201`, filled down to row 801.
4. Build EMA20 and EMA50 the same way: seeds `AVERAGE(B2:B21)` and `AVERAGE(B2:B51)`, factors 2/21 and 2/51.
5. Read the last row; for the slope, compare the EMA50 value in row 801 with row 791.

### B9.3 Test cases

**Status of every test below: specified, not executed.** No Q-MAP scanner code exists. The expected values were produced by an exploratory calculation (or, for T-EMA-01 and T-EMA-16, by arithmetic re-checked in the review cycles); none of them is evidence that Q-MAP has run the test, and **none has been independently verified against the source data**. The methodology is approved, so the values stand as targets once independently reproduced (§B9.2).

| ID | Objective | Input | Expected | Pass if | G-03 effect |
|---|---|---|---|---|---|
| T-EMA-01 | EMA arithmetic | B9.1 closes, N = 3 | 416.95, 421.025, 430.9375, 435.36875 | Exact to 4 dp | No |
| T-EMA-02 | Bearish reference | CONCOR, analysis 06-Nov-26, defaults | Window 17-Aug-23 to 06-Nov-26; EMA20 432.7297, EMA50 452.6585, EMA200 486.4492, EMA50 ten bars earlier 466.7276; answers +1 −1 −1 −1 −1 −1; net −4; score 16.67; BEARISH | Equal to Excel (B9.2) to 4 dp; score exact | **Yes**: default result `INVALID_DATA` (04-Jun-24 issue); the values apply after 04-Jun-24 is `VERIFIED_OK` |
| T-EMA-03 | Neutral reference | INFY, 06-Nov-26 | Window 17-Aug-23 to 06-Nov-26; 1,132.2614 / 1,108.5365 / 1,203.8765 / 1,084.5193; answers +1 +1 −1 +1 −1 +1; net +2; score 66.67; NEUTRAL | As above | No (source-verified: no ±15% move in the window) |
| T-EMA-04 | Fully bullish reference | INFY, 03-Feb-26 | Window starts 16-Nov-22; 1,646.1038 / 1,617.6051 / 1,589.1800 / 1,598.2591; all +1; score 100; BULLISH | As above | No (source-verified: no ±15% move in the window) |
| T-EMA-05 | Bullish with a bearish long-term answer | CONCOR, 09-Sep-26 | Window starts 21-Jun-23; 509.8872 / 504.0989 / 506.0167 / 502.3052; answers +1 +1 +1 +1 −1 +1; net +4; 83.33; BULLISH | As above | **Yes**: as T-EMA-02 |
| T-EMA-06 | Insufficient history | CONCOR, 31-Dec-01 | `INSUFFICIENT_DATA` (690 bars available, 800 needed); no score | Exact | No |
| T-EMA-07 | First date with enough history | CONCOR | First analysis date with status `OK` (no blocking issue) = **06-Jun-02** | Exact | No: no move beyond ±15% before 06-Jun-02 (source-verified) |
| T-EMA-08 | Continuity break blocks | CONCOR, 30-Jun-14 (window 11-Apr-11 to 30-Jun-14 contains 06-Sep-13, issue open with `affects_continuity`) | `INVALID_DATA` naming the issue | Exact | Default result under G-03 (changes only if the Owner verifies 06-Sep-13) |
| T-EMA-09 | Recovery after the break | CONCOR, 07-Dec-16 then 08-Dec-16 | 07-Dec-16: `INVALID_DATA` (window still contains 06-Sep-13); 08-Dec-16: `OK` (window starts **10-Sep-13** — corrected in v1.6; the source has no 09-Sep-13 record) | Exact | As T-EMA-08 |
| T-EMA-10 | Exact tie counts 0 | Fixture: constant closes of 100.00 for 800 bars | Every EMA = 100; all answers 0; net 0; score 50; NEUTRAL | Exact — *Expected result is mathematically correct, but a plain floating-point implementation returns net −2 (EMA200 = 100.0000000000001); passing requires the D-EMA-12 precision rule (document 13, EMA-F1).* | No (fixture) |
| T-EMA-11 | Monotonic rise | Fixture: closes rising by 1.00 per bar from 100.00 | All answers +1; score 100 | Exact | No (fixture) |
| T-EMA-12 | Monotonic fall | Fixture: closes falling by 0.10 per bar from 1,000.00 | All answers −1; score 0 | Exact | No (fixture) |
| T-EMA-13 | Determinism | T-EMA-02 run twice | Identical result sections | Byte-identical | Inherits T-EMA-02 |
| T-EMA-14 | Held revision does not change the result | After T-MNT-03 (held CONCOR revision) | Same result as T-EMA-02 (in either state), plus a `HELD_REVISION_EXISTS` message | Exact | **Yes**: as T-EMA-02 |
| T-EMA-15 | Contract validation | Any `INSUFFICIENT_DATA` result | Score null; passes `validate_result` | Pass | No |
| T-EMA-16 | Classification and score cover every net count (new in v1.2) | Each net value −6, −5, … , +6 | Scores 0, 8.33, 16.67, 25, 33.33, 41.67, 50, 58.33, 66.67, 75, 83.33, 91.67, 100 (2 dp). States: −6/−5/−4 BEARISH; −3 NEUTRAL_LEANING_BEARISH; −2…+2 NEUTRAL; +3 NEUTRAL_LEANING_BULLISH; +4/+5/+6 BULLISH | All 13 exact; no net value unclassified | No (logic test) |
| T-EMA-17 | Stale data (new in v1.3; depends on D-EMA-11) | CONCOR, analysis date 10-Nov-26, active data ending 06-Nov-26, with 09-Nov-26 and 10-Nov-26 trading days in the calendar | Under the proposed D-EMA-11: `INSUFFICIENT_DATA`, message "data ends 06-Nov-26; analysis date 10-Nov-26", no score. Under the alternative: `OK` with `facts.analysis_date` 06-Nov-26 and the T-EMA-02 values. | Exact for the approved option | Yes (inherits T-EMA-02 under the alternative) |
| T-EMA-18 | Open-only anomaly blocks under G-03 (new in v1.3; values added v1.6) | CONCOR, analysis date 31-Dec-07 (window 14-Oct-04 – 31-Dec-07 contains 15-May-06, whose open moved +16.0% and close −3.6%; no other ±15% move in the window — source-verified) | **`INVALID_DATA`** naming the 15-May-06 issue — this is the expected result. **Conditional values, valid only after the Owner verifies 15-May-06 and marks it `VERIFIED_OK`:** close 246.61; EMA20 236.3180; EMA50 241.2234; EMA200 252.5792; EMA50 ten bars earlier 244.1076; answers +1 +1 −1 −1 −1 −1; net −2; 33.33; NEUTRAL. These are **not** an accepted scanner result while the block stands. | Status exact; conditional values exact to 4 dp | **Yes** |

T-EMA-18's window has been checked against the source: the only ±15% move inside it is 15-May-06. T-EMA-07 does not depend on G-03: CONCOR has no open or close move beyond ±15% before 06-Jun-02 (source-verified). Its 87 missing days in 1998–2001 are missing days, not continuity issues. **T-EMA-02, 05, 13 and 14** have windows containing 04-Jun-24: their default result is `INVALID_DATA`, and their listed values apply after the Owner verifies that occurrence. **T-EMA-08, 09 and 18** describe the default blocking behaviour.

## B10. Known limitations

1. **Coarse score.** At most 13 possible values (steps of 8.33); in practice mostly the seven even-net values, because odd nets need an exact tie.
2. **Sensitivity at the lines.** A change of a few paise can flip an answer (CONCOR 09-Sep-26: price 0.02% above its EMA20). D-EMA-07 offers a near-the-line allowance.
3. **Lag.** EMAs, especially the 200-day, react slowly. That is inherent to the method.
4. **Adjusted prices.** EMAs over back-adjusted history (a working hypothesis) are internally consistent. A **held** revision means results use the older active data until the revision is approved.
5. **Continuity blocking (G-03, approved).** Every ±15% move in a window blocks the score until the Owner verifies it, including genuine market-wide moves (e.g. CONCOR 04-Jun-24) and open-only data errors. Results for affected stocks stay unavailable until the Owner's review.
6. **Indices.** Not proposed for version 1. NIFTY's 1-minute history from 09-Jan-25 gives about 450 daily bars, fewer than 800.

*End of document 10, v1.7.*
