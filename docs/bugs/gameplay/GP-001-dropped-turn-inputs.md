# GP-001: Quick turn combos drop the first input

| | |
| --- | --- |
| Severity | Medium |
| Category | Gameplay (player-facing) |
| Area | Input / `entities/snake.py` |
| Status | Fixed |
| Branch | `docs/setup-agent-skills` |
| Found by | Code review |
| Fixed in | `entities/snake.py` |

## Summary
The snake stored a single `next_direction`. Two key presses inside one move interval (about 100 ms at Normal speed) overwrote each other, so fast maneuvers such as up-then-left did not register as two turns.

## Steps to reproduce
1. Move right at Normal speed.
2. Press Up and then Left in quick succession, inside one move interval.
3. Left is rejected as a reverse of the current direction, so only Up registers, and only the first turn happens.

## Expected vs actual
- Expected: the snake goes up one cell, then left.
- Actual: the second press is lost or can silently overwrite the first.

## Root cause
Reversal was validated against `self.direction` (the direction of the last move), not against the most recent pending input, and only one pending input could exist.

## Fix
Replaced `next_direction` with a `direction_queue` of at most two turns. Each new input is validated against the last queued direction. Duplicates and reversals of the queued direction are ignored.

## Regression test
`tests/test_snake.py::test_turns_are_buffered_across_moves`, `test_reversal_checked_against_queued_direction`, `test_queue_is_capped`
