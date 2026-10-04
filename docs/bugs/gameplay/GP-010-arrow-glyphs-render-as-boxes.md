# GP-010: Arrows in the upgrade previews render as boxes

| | |
| --- | --- |
| Severity | Low |
| Category | Gameplay (player-facing) |
| Area | UX / `systems/upgrade_system.py`, `ui/screens.py` |
| Status | Fixed |
| Branch | `refactor/improve-codebase-architecture` (also on `main`) |
| Found by | Playtest (human) |
| Build | `5817af9` |

## What the player experiences
The before-and-after line on each upgrade card, for example `HP: 5 → 6`, shows a box with an X in place of the arrow. The speed-select hint `← →  navigate` has the same problem.

## Steps to reproduce
Clear wave 1 and look at the bottom line of any upgrade card, or open the speed-select screen.

## Expected vs actual
- Expected: a readable arrow between the old and new value.
- Actual: a "missing glyph" box.

## Player impact
The preview of what an upgrade does is harder to read at the moment the player is choosing.

## Root cause
The UI font, Poppins, has no glyphs for `→` (U+2192) or `←` (U+2190). Neither does pygame's fallback font `freesansbold.ttf`, which is used when Poppins isn't installed.

## Fix
- Upgrade previews use `->`.
- The speed-select hint reads `Left / Right  navigate`.

## Verification
`tests/test_game.py::test_every_rendered_character_has_a_glyph` records every string drawn on every screen, plus every upgrade's name, description and preview. It checks each character against the Poppins regular and bold files that pygame resolves, or the fallback font when Poppins is absent. It failed before the fix on `←` and `→`.
