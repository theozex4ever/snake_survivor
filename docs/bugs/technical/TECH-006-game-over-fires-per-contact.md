# TECH-006: Game-over handling fires once per overlapping enemy

| | |
| --- | --- |
| Severity | Medium |
| Category | Technical (software defect) |
| Area | Game flow / `game.py` |
| Status | Fixed |
| Branch | `fix/gameplay-bugs-tests-bug-tracker` |
| Found by | PR review |
| Fixed in | `game.py` |

## Summary
The fix for [TECH-001](TECH-001-enemy-death-skips-game-over.md) put `if not self.snake.alive: self._on_game_over()` inside the enemy-contact loop. After the lethal contact the condition stays true, so each further overlapping enemy replayed the game-over sound and the save.

## Steps to reproduce
Set HP to 1 and put three enemies on the head. One update plays `game_over` three times.

## Root cause
The death check ran per enemy without leaving the loop.

## Fix
`break` out of the contact loop after the lethal contact.

## Not changed
`player_hurt` still plays for contacts during invulnerability, when no damage is dealt. That predates this work and affects feel, so it is left for a design decision.

## Regression test
`tests/test_game.py::test_game_over_fires_once_with_simultaneous_lethal_contacts`
