# GP-008: "No food in the game" (not reproduced)

| | |
| --- | --- |
| Severity | n/a |
| Category | Gameplay (player-facing) |
| Area | UX |
| Status | Informative (no fix) |
| Branch | `refactor/improve-codebase-architecture` |
| Found by | Playtest (human) |
| Build | `5817af9` |

## What the player reported
The tester saw no food on the board, possibly for 5 runs in a row, and guessed it was hiding in the upper corner.

## What we found
- **Not reproduced.** In a run started on this build in a real window on KDE Wayland, the food was clearly visible.
- **Food placement is uniform.** Across 2,000 runs started through `Game` on this branch and on `main`, starting food landed on about 1,150 distinct cells and no cell came up more than 8 times.
- **Food can spawn under the top-left HUD panel**, where it is nearly invisible behind the text. This happens to about 3.4% of spawns (cells the panel fully or partly covers). Five runs in a row would be about 1 in 20 million, so it doesn't explain the report.
- Possible causes we didn't check: the window not fitting the tester's screen at their display scaling (part of the board cut off), or a compositor that shows the transparency holes from [GP-009](GP-009-black-squares-on-alpha-windows.md) during play.

## Decision
Closed as informative at the owner's request. Food spawning under the HUD panel is a real but rare annoyance and was not fixed. If it comes back, ask the tester for a screenshot, their resolution and display scaling, and whether all four edges of the board were visible.
