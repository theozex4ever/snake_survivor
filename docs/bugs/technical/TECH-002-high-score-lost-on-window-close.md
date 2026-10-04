# TECH-002: High score lost when closing the window

| | |
| --- | --- |
| Severity | Medium |
| Category | Technical (software defect) |
| Area | Persistence / `game.py` |
| Status | Fixed |
| Branch | `docs/setup-agent-skills` |
| Found by | Code review (also listed as a known limitation in the README) |
| Fixed in | `game.py` |

## Summary
The high score was written only when the player pressed R after game over.

## Steps to reproduce
1. Beat the high score and die.
2. Close the window instead of pressing R.
3. Relaunch: the old record is shown.

## Expected vs actual
- Expected: a new record survives however the session ends.
- Actual: the record is lost.

## Root cause
`_save_high_score()` was called from only one place, the R key handler.

## Fix
Save on death (via `_on_game_over`, see TECH-001) and on `pygame.QUIT`.

## Regression test
`tests/test_game.py::test_quit_saves_high_score`, `test_wall_death_saves_high_score`
