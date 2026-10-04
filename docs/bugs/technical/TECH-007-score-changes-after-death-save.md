# TECH-007: Score keeps changing after the death save

| | |
| --- | --- |
| Severity | Medium |
| Category | Technical (software defect) |
| Area | Persistence / `game.py` |
| Status | Fixed |
| Branch | `fix/gameplay-bugs-tests-bug-tracker` |
| Found by | PR review |
| Fixed in | `game.py` |

## Summary
`update()` carried on after a movement death (wall or self hit), so shooting and bullet collisions in the same frame could still add score. The high score had already been saved, so the displayed final score could exceed the saved one. The next restart or quit repaired it. This is a gap in the save-on-death behaviour added for [TECH-002](TECH-002-high-score-lost-on-window-close.md).

## Steps to reproduce
Score 40, hit a wall, and have a bullet overlapping a 1-HP enemy in the same frame: the screen shows 60, the saved high score is 40.

## Root cause
Nothing stopped the frame after the snake died.

## Fix
`update()` returns immediately after a movement death, so the score is final when it is saved.

## Regression test
`tests/test_game.py::test_movement_death_freezes_frame_so_saved_score_is_final`
