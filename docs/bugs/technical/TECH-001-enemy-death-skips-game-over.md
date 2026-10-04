# TECH-001: Dying to an enemy skips game-over sound and high-score save

| | |
| --- | --- |
| Severity | High |
| Category | Technical (software defect) |
| Area | Game flow / `game.py` |
| Status | Fixed |
| Branch | `docs/setup-agent-skills` |
| Found by | Code review |
| Fixed in | `game.py` |

## Summary
Game-over handling only ran in the movement branch (wall and self collision). Losing the last heart to an enemy touch killed the snake without it.

## Steps to reproduce
1. Reach 1 HP with a non-zero score.
2. Let an enemy touch the head.
3. Press R at the game-over screen.

## Expected vs actual
- Expected: game-over sound plays and a new best score is recorded.
- Actual: no game-over sound. The score was only saved if you pressed R, and never if you closed the window instead. See TECH-002.

## Root cause
`sound_mgr.play("game_over")` lived inside `if not self.snake.alive` after `snake.move()`. The enemy-contact loop never checked for death.

## Fix
Added `Game._on_game_over()` (sound plus high-score save) and call it from both death paths.

## Regression test
`tests/test_game.py::test_lethal_contact_saves_high_score`
