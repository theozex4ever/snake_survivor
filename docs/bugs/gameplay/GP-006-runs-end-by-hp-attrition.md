# GP-006: Every run is decided by a fixed hit budget

| | |
| --- | --- |
| Severity | Medium |
| Category | Gameplay (player-facing) |
| Area | Balance / health |
| Status | Open (design decision needed) |
| Branch | `docs/setup-agent-skills` |
| Found by | Playtest (headless bot, see [baseline](../playtests/2026-10-04-baseline.md) sections 1 and 2) |
| Build | `3b375eb` plus working-tree fixes |

## What the player experiences
Health only goes down. There is no way to recover it, so a run is a countdown that ends after a predictable number of enemy hits.

## Expected vs actual
- Expected: skill in steering, positioning, and upgrade choice changes how long a run lasts.
- Actual: 172 of 240 bot runs ended after exactly 5 or 6 enemy hits. Mean hits by Extra Heart count: 0 hearts 4.94, 1 heart 6.0, 2 hearts 6.92, 3 hearts 8.0. Starting speed barely moved the median wave (5 to 8 for all eight speed/profile combinations). Careful play gained about 2 waves over greedy play.

## Player impact
Dodging well only delays the countdown a little. Late waves feel inevitable rather than earned, and the Extra Heart upgrade is a flat "+1 hit".

## Root cause
Enemy contact costs 1 HP each, nothing restores HP except the Extra Heart upgrade, and enemy count grows as `3 + 2 * wave`.

## Suggested directions
Heal a heart every N foods, or let a clean wave restore one. Alternatively reduce contact damage as enemies die on touch anyway. Verify with the bot that the hit-count distribution widens and that careful play gains more over greedy play.

## Verification
Re-run `python tools/playtest.py --runs 30 --speed Normal --profile careful` and compare the hits distribution and the careful-versus-greedy gap.
