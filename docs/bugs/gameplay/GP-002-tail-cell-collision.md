# GP-002: Moving into the vacating tail cell kills the snake

| | |
| --- | --- |
| Severity | Medium |
| Category | Gameplay (player-facing) |
| Area | Movement / `entities/snake.py` |
| Status | Fixed |
| Branch | `docs/setup-agent-skills` |
| Found by | Code review (also listed as a known limitation in the README) |
| Fixed in | `entities/snake.py` |

## Summary
Self-collision was checked against the whole body, including the tail cell, even though the tail leaves that cell on the same move.

## Steps to reproduce
1. Coil the snake into a 2x2 loop where the head sits next to the tail.
2. Move the head into the tail's cell.

## Expected vs actual
- Expected: the move is safe, as in classic Snake, because the tail moves away.
- Actual: the run ends immediately.

## Root cause
`if new_head in self.segments` ran before the tail was popped.

## Fix
Collision is checked against `segments[:-1]` unless `grow_pending > 0`, when the tail stays in place.

## Regression test
`tests/test_snake.py::test_moving_into_vacating_tail_is_safe`, `test_moving_into_tail_while_growing_kills`
