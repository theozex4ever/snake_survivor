# GP-009: Black squares behind the hearts and food on the upgrade screen

| | |
| --- | --- |
| Severity | Medium |
| Category | Gameplay (player-facing) |
| Area | Rendering / `game.py`, `ui/screens.py` |
| Status | Fixed |
| Branch | `refactor/improve-codebase-architecture` (also on `main`) |
| Found by | Playtest (human) |
| Build | `5817af9`, KDE Plasma on Wayland, pygame 2.6.1, SDL 2.32 |

## What the player experiences
On the "Choose an Upgrade" screen, the HUD panel behind the hearts turns into a solid black rectangle. The glow around the food also turns into a black square.

## Steps to reproduce
On a KDE Wayland session, clear wave 1 and wait for the upgrade cards. A compositor screenshot (`spectacle -b -n -a`) shows the black rectangles.

## Expected vs actual
- Expected: the whole frame is dimmed evenly behind the cards.
- Actual: the HUD panel and the food glow are black.

## Player impact
The HUD looks broken every time the player levels up.

## Root cause
On this display, `pygame.display.set_mode` returns a window surface with an alpha channel (ARGB). Every plain `pygame.Surface(...)` inherits that format, including `game_surface`. When a translucent (`SRCALPHA`) surface is blitted onto such a surface, pygame leaves the destination alpha at **0**, so the HUD panel, food glow and anti-aliased text become alpha-0 holes. During play KWin ignores the window's alpha, so nothing shows. On the upgrade screen, the dim overlay is blended over those holes and they come out black.

The dummy video driver used by the tests has no alpha channel, so the tests could never see this. The bug is on `main` too, so it predates the Run refactor.

## Fix
`Game` draws everything on opaque canvases (`_opaque_surface()`, an RGB surface with no alpha mask) and copies the canvas to the window once per frame in `draw()`. The screen functions no longer call `pygame.display.flip()` themselves.

## Verification
- `tests/test_game.py::test_frames_are_opaque_on_windows_with_an_alpha_channel` replaces the window with an ARGB surface and checks that every pixel of every screen has alpha 255. It failed before the fix.
- Rechecked by hand with a Spectacle capture on KDE Wayland: the upgrade screen dims evenly.
