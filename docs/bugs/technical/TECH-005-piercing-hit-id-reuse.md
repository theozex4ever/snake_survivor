# TECH-005: Piercing bullets track enemies by recyclable `id()`

| | |
| --- | --- |
| Severity | Medium |
| Category | Technical (software defect) |
| Area | Combat / `game.py`, `entities/enemy.py` |
| Status | Fixed |
| Branch | `fix/gameplay-bugs-tests-bug-tracker` |
| Found by | PR review |
| Fixed in | `entities/enemy.py`, `game.py` |

## Summary
The fix for [GP-003](../gameplay/GP-003-piercing-rehits-enemy.md) stored `id(enemy)` in `Bullet.hit_ids`. Python can reuse an `id()` after an object is freed. A piercing bullet that killed one enemy could therefore ignore a new enemy that received the same ID.

## Steps to reproduce
A stationary piercing bullet kills a 1-HP enemy. The enemy is removed and a new one is created at the same spot. The new enemy can get the old ID and the bullet skips it.

## Root cause
`id()` is unique only among objects that are alive at the same time.

## Fix
`Enemy.uid` comes from a process-wide counter and is never reused. `hit_ids` stores `uid`s. (Storing enemy objects instead would not work: `Enemy` is a non-frozen dataclass and so is unhashable.)

## Regression test
`tests/test_game.py::test_piercing_bullet_still_hits_new_enemy_after_previous_one_dies`, `test_enemy_uids_are_unique_across_removed_enemies`
