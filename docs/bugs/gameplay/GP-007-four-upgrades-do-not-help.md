# GP-007: Four upgrades give no measurable benefit

| | |
| --- | --- |
| Severity | Medium |
| Category | Gameplay (player-facing) |
| Area | Balance / upgrades |
| Status | Open (design decision needed) |
| Branch | `docs/setup-agent-skills` |
| Found by | Playtest (headless bot, see [baseline](../playtests/2026-10-04-baseline.md) section 3) |
| Build | `3b375eb` plus working-tree fixes |

## What the player experiences
Piercing Shot, Swift Snake, Thick Skin and Extra Heart are offered like the strong upgrades, but taking them every time does not get a run further than picking at random.

## Expected vs actual
Mean wave over 60 runs per policy, against a random-pick control at 8.73 (control and Piercing Shot re-run on the fixed build):

| Upgrade | Mean wave |
| --- | --- |
| Extra Heart | 8.33 |
| Thick Skin | 7.58 |
| Swift Snake | 7.17 |
| Piercing Shot | 7.20 |

All four are below the control. The control includes strong upgrades, so the comparison is not "worse than nothing", but none of them reaches even the mean of a random pick.

## Player impact
Four of the six upgrades in the pool are weak picks, so most upgrade screens offer at least one dud, which makes the "three upgrades" screen feel less meaningful.

## Root cause (hypotheses, not yet tested)
- Swift Snake raises movement speed, which makes the snake harder to steer and does nothing for survival or damage.
- Thick Skin adds 0.3 s of invulnerability, but enemies are destroyed on contact anyway, so the benefit is small.
- Piercing Shot only matters when enemies line up, and enemies converge from all sides rather than in lines.
- Extra Heart is one hit out of a run that already ends after about 6 (see GP-006).

## Caveat
Piercing Shot was re-measured on the build with both [GP-003](GP-003-piercing-rehits-enemy.md) and [TECH-005](../technical/TECH-005-piercing-hit-id-reuse.md) fixed (7.15 before the TECH-005 fix, 7.20 after). The other three upgrades were measured before those fixes, which do not touch them.

## Verification
Re-run the preference experiment for each upgrade after rebalancing, using the commands in the baseline report.
