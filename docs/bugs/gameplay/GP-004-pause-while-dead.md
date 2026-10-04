# GP-004: Game can be paused after death

| | |
| --- | --- |
| Severity | Low |
| Category | Gameplay (player-facing) |
| Area | Input / `game.py` |
| Status | Fixed |
| Branch | `docs/setup-agent-skills` |
| Found by | Code review |
| Fixed in | `game.py` |

## Summary
Pressing P on the game-over screen opened the pause overlay on top of it. Resuming returned to the game-over state, but the R prompt could not be used while paused.

## Steps to reproduce
Die, then press P.

## Expected vs actual
- Expected: P does nothing on the game-over screen.
- Actual: the pause overlay appears.

## Root cause
The P handler only checked `state == "playing"`, and a dead snake still leaves the state as `playing`.

## Fix
The handler also requires `self.snake.alive`.

## Regression test
`tests/test_game.py::test_pause_blocked_when_dead`
