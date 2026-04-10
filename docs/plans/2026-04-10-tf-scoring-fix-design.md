# Fix: Transnational Facilitation Scoring

**Date:** 2026-04-10
**Status:** Validated (revised after pushback review)

## Problem

FSI Value (secrecy laws x offshore finance volume) is extremely right-skewed
-- USA=2018, #2 Switzerland=1398, median ~161. Linear min-max normalization
gives the US a perfect 100 and compresses all other countries, producing absurd
comparisons (USA 100 vs Cayman Islands 25, Panama 29).

The root cause: FSI Value conflates economic scale with extractive policy
choices. The US scores highest because it has the world's largest financial
sector, not because its secrecy laws are the most extreme. Log transformation
was considered but still leaves the US at 100 (it's the max under any
monotonic transform) while inflating the middle (median 61).

## Change

Switch the TF domain score from FSI Value to the **FSI secrecy score, used
raw (no min-max normalization)**. The secrecy score is TJN's own 0-100 measure
of how much secrecy a jurisdiction's laws enable, independent of economic
scale. It is already on a 0-100 scale consistent with the index's convention.

The FSI Value (secrecy x volume) is retained as a **displayed context fact**
in the indicator detail, so analysts can still see the impact measure. It is
not used for scoring.

### Rationale for raw (no min-max normalization)

The secrecy score has a narrow empirical range (29-80, mean 64, stdev 10).
Min-max normalization would stretch this to 0-100, inflating scores across the
board and destroying TJN's absolute judgments (a "moderate secrecy" score of 55
would become ~51 after normalization, then get averaged with other domains that
ARE min-max normalized). Using the raw score preserves the fact that no country
is at the extremes of the 0-100 scale — which is TJN's considered assessment.

## Expected Impact

Computed from actual data, not estimated:

| Country | Current TF | New TF | Delta |
|---------|:---:|:---:|:---:|
| USA | 100 | 69 | -31 |
| Switzerland | 69 | 75 | +6 |
| Singapore | 61 | 68 | +7 |
| Panama | 29 | 78 | +49 |
| Cayman Islands | 25 | 73 | +48 |
| BVI | 28 | 72 | +44 |
| UK | 24 | 45 | +21 |
| Denmark | 4 | 39 | +35 |
| Norway | 12 | 55 | +43 |

Key shifts:

- **USA drops from 100 to 69** -- still high (correctly so: Delaware LLCs,
  South Dakota trusts, historic beneficial ownership opacity) but no longer an
  absurd outlier
- **Traditional tax havens rise significantly** -- Panama (78), Cayman (73),
  BVI (72) now score higher than the USA, reflecting their purpose-built
  secrecy regimes
- **Switzerland stays similar** -- 69 to 75, modest increase
- **Clean jurisdictions rise modestly** -- Denmark 39, UK 45, reflecting that
  even transparent countries have some secrecy dimensions. These are below
  the global median (65), which is reasonable
- **US composite drops from 40 to 35** -- no longer inflated by the TF outlier

### Limitation

This approach deliberately drops the scale dimension. The US facilitates more
total secrecy than Bermuda by virtue of its financial sector size, but this is
no longer captured in the score. The FSI Value context fact partially
compensates, and the TODO tracks adding more TF indicators in the future.

## Additional Changes

### METHODOLOGY.md

1. Update the Transnational Facilitation section: document the switch from FSI
   Value to secrecy score, the rationale for using raw scores, and the FSI
   Value context fact.

2. Add a "Known Limitations" note to the Political Capture section: V-Dem
   measures formal democratic quality well but systematically underweights
   legal capture mechanisms (campaign finance deregulation, lobbying industry,
   revolving door) that are the primary mode of political capture in advanced
   democracies.

### scratch/TODO.md

Add a Medium-priority item for sourcing lobbying/campaign finance data to
improve political_capture scoring in advanced democracies. (Already done.)

### Code changes (score_countries.py)

- Replace FSI Value normalization with raw secrecy score as the domain score
- Keep FSI Value as a context fact in the indicator detail (already displayed)
- Update indicator metadata (INDICATOR_QUESTIONS, INDICATOR_DETAIL, source
  keys) to reflect the secrecy score as the primary indicator
- The secrecy score data already flows through the pipeline (currently stored
  in fsi_secrecy dict) -- just needs to be promoted from display fact to
  scored indicator

### Validation

- Re-run `python score_countries.py` to regenerate scores.json
- Run `make all` and verify zero errors
- Spot-check key countries (USA, Switzerland, Cayman, Panama, Denmark) against
  expected values above

### No changes to

The frontend (js/app.js, css), the fetcher pipeline, or any other domain's
scoring.
