# README Update Design

**Date:** 2026-02-11
**Status:** Implemented

## Goals

1. **Completeness** — Add 15 missing command groups from later implementation phases
2. **Presentation** — Better reader experience with scannable grouped layout
3. **Trimming** — Remove duplication with existing docs/ files

## Key Decisions

- **Command overview**: Grouped summary table by domain (16 rows) instead of per-command table (was 50+ rows, still incomplete). Links to `docs/COMMANDS.md` for subcommand detail.
- **Features list**: Consolidated from 20 items to 5 high-level highlights.
- **Duplicated sections** (VM Templates, Configuration, Shell Completion, Output Formats): Replaced with teaser + link to the relevant doc.
- **Global Options and Exit Codes**: Kept as small tables — useful for quick reference, minimal duplication cost.
- **Contributing**: Trimmed redundant "Getting Started" header; kept dev setup commands and guidelines.
- **Documentation links**: Added Architecture and Command Reference (previously missing).

## Result

- 411 lines → 152 lines (63% reduction)
- All 27 command groups now represented
- No content lost — everything links to the appropriate doc
