# TECH-008: Playtest bot miscounted hits and food

| | |
| --- | --- |
| Severity | Low (tooling, affected reported statistics) |
| Category | Technical (software defect) |
| Area | `tools/playtest.py` |
| Status | Fixed |
| Branch | `fix/gameplay-bugs-tests-bug-tracker` |
| Found by | PR review |
| Fixed in | `tools/playtest.py` |

## Summary
Two measurement errors in the bot:
- The final death always added one "hit", so wall and self deaths were counted as enemy hits.
- A food pickup was detected by a score change of exactly 10, so a pickup in the same frame as a bullet kill (change of 30) was missed.

## Impact
Only 7 of the 240 baseline runs were self-collision deaths, and food counts are not cited in any report. The [GP-006](../gameplay/GP-006-runs-end-by-hp-attrition.md) conclusion did not change, but its numbers were refreshed.

## Fix
Hits count actual HP decreases (whether or not the snake survives) and food counts a change of `game.food`. The per-frame accounting moved into `advance()` so it can be tested. The same review also caught a test that guarded on a non-existent `muted` attribute and so never asserted anything: it now reads `is_muted`.

## Regression test
`tests/test_playtest_tool.py` (wall death is not a hit, contact death is, food counts alongside a kill, and a smoke test of `play_run`), `tests/test_game.py::test_mute_toggle`
