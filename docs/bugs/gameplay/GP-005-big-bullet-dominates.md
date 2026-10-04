# GP-005: Big Bullet dominates every other upgrade

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
Upgrade choice is not a real choice. Taking Big Bullet every time it is offered carries a run far past every other option.

## Steps to reproduce
```bash
python tools/playtest.py --runs 60 --speed Normal --profile careful --upgrades prefer:big_bullet --seed 7
python tools/playtest.py --runs 60 --speed Normal --profile careful --upgrades prefer:faster_fire --seed 7
```

## Expected vs actual
- Expected: the six upgrades lead to roughly comparable progress, with trade-offs.
- Actual: mean wave reached over 60 runs: Big Bullet 14.35, Faster Fire 10.0, random picks 8.73. The other four are between 7.20 and 8.33.

## Player impact
Players who notice it stop reading the cards. Runs with Big Bullet become long and high-variance (SD 6.9). One run reached wave 21.

## Root cause (hypothesis, not yet tested)
Big Bullet adds +1 damage and +2 radius together. Enemy HP is only 2 at wave 1 and grows by 1 every two waves, so +1 damage is a large multiplier early, and a larger hitbox makes auto-aimed shots land more often. No other upgrade multiplies kill speed.

## Suggested directions
Split the upgrade into separate damage and size upgrades, give it diminishing returns, or scale enemy HP faster once damage is stacked. Re-run the preference experiment after any change.

## Verification
Re-run the commands above. Done when the best and worst preference results are within about 1.5x of each other.
