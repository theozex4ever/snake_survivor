# GP-003: Piercing bullets re-hit the same enemy every frame

| | |
| --- | --- |
| Severity | High |
| Category | Gameplay (player-facing) |
| Area | Combat / `game.py`, `entities/bullet.py` |
| Status | Fixed |
| Branch | `docs/setup-agent-skills` |
| Found by | Code review (also listed as a known limitation in the README) |
| Fixed in | `game.py`, `entities/bullet.py` |

## Summary
A bullet moves about 8.7 px per frame but overlaps an enemy for several frames (combined radius of about 17 px). Each overlapping frame counted as a new hit.

## Steps to reproduce
1. Take Piercing Shot.
2. Shoot an enemy with more than 1 HP.

## Expected vs actual
- Expected: the bullet damages the enemy once and passes through to the next target.
- Actual: the bullet damaged the same enemy on consecutive frames and used its pierce allowance on it. It could be consumed before reaching a second enemy, and Piercing Shot was close to worthless.

## Root cause
No per-bullet memory of which enemies it had already hit.

## Fix
`Bullet.hit_ids` records `id(enemy)` for each hit. Enemies already in the set are skipped.

## Regression test
`tests/test_game.py::test_piercing_bullet_hits_each_enemy_once` (the enemy's HP drops by exactly 1 over five frames of overlap)
