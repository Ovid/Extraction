# Changelog Design

## Goal

Create a curated, researcher-facing changelog that tracks significant
user-visible and methodology changes to the Extraction Index.

## Decisions

- **Format:** Milestone-based with date ranges, no version numbers.
- **Audience:** Researchers and visualization users, not contributors.
- **Location:** `CHANGELOG.md` in project root.
- **Entry style:** One-sentence plain-language bullets. No category
  subheadings (Added/Fixed/etc.).
- **Scope:** User-visible and methodology changes only. Skip internal
  refactors, code reviews, test infrastructure, data regenerations,
  formatting, and merge commits.
- **Versioning:** None. Milestones and dates are sufficient for a
  continuously-updated web visualization. If pinnable references are
  needed later (e.g., academic citations), commit hashes or dates serve
  that purpose.

## Milestones (from git history)

1. **Initial Build** (2026-04-06)
2. **Visualization & UX Polish** (2026-04-06)
3. **Scoring Accuracy Overhaul** (2026-04-07)
4. **Financial & Economic Data** (2026-04-08 -- 2026-04-10)
5. **Transnational Facilitation Redesign** (2026-04-10)
6. **Data Quality & Security Hardening** (2026-04-11)

## Maintenance

CLAUDE.md gets a one-line rule: significant user-visible or methodology
changes require a CHANGELOG.md entry, similar to the existing
METHODOLOGY.md rule.
