# TECH-004: Frame-time spikes skip moves and collisions

| | |
| --- | --- |
| Severity | Low |
| Category | Technical (software defect) |
| Area | Main loop / `game.py` |
| Status | Fixed |
| Branch | `docs/setup-agent-skills` |
| Found by | Code review |
| Fixed in | `game.py` |
| Test | None. The fix is a one-line clamp in the real-time loop. |

## Summary
`dt` was passed to `update` unclamped. After a stall (window drag, disk hiccup), enemies and bullets teleported by `speed * dt` in one step, which can pass through the head's collision radius. The snake also moved only once for the whole stall, because movement uses `if`, not `while`.

## Fix
`dt = min(clock.tick(FPS) / 1000.0, MAX_FRAME_DT)` with `MAX_FRAME_DT = 0.05`.
