# Snake Survivor

**Classic Snake meets a wave survival shooter.** Steer, collect food, and stay alive while your snake automatically fires at the nearest enemy. Clear a wave, pick an upgrade, and build a stronger snake for the next round.

Built with Python and Pygame. The game window and menu use the title **Snake Shooter**.

## Features

- Grid-based Snake movement with four starting speeds: Relaxed, Normal, Fast, and Blazing.
- Automatic targeting and shooting, so you can focus on movement.
- Enemy waves with increasing numbers, health, and movement speed.
- Three randomly offered upgrades after each completed wave.
- A dark pastel interface with health hearts, particle effects, bullet glow, and screen shake.
- Procedurally generated sound effects, a mute toggle, and local high scores.

## Getting started

You need Python 3 with `venv` and `pip`, plus a desktop display to play. The code was smoke-tested with Python 3.14.7 and Pygame 2.6.1.

From the project directory, create and activate a virtual environment:

```bash
python -m venv .venv
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependency and launch the game:

```bash
python -m pip install -r requirements.txt
python main.py
```

The window is 1100 × 720 pixels and targets 60 FPS. Poppins is used when installed; Pygame falls back to an available font. Missing WAV effects are generated automatically in `assets/sfx/`. If audio initialization fails, the game continues silently.

## Controls

| Action | Input |
| --- | --- |
| Start from the menu | Enter or Space |
| Browse starting speeds | Left / Right arrows or A / D |
| Confirm selected speed | Enter or Space |
| Select a speed and start immediately | 1–4 |
| Steer | Arrow keys or WASD |
| Pause during play or upgrade selection | P |
| Resume | P or Escape |
| Pick an upgrade | 1–3 or click a card |
| Toggle sound in speed selection, gameplay, upgrades, or pause | M |
| Return to the menu after game over | R |
| Quit | Close the window |

Shooting is automatic. Directly reversing your movement direction is blocked. Up to two turns are buffered, so quick combos such as up-then-left register on consecutive moves.

## How to play

1. Choose your starting speed. Normal moves at 10 cells per second.
2. Collect food to grow and earn **10 points** per pickup.
3. Dodge enemies while automatic shots target the nearest living enemy. Each enemy killed by a bullet earns **20 points**.
4. Clear every enemy in a wave, then choose one of three upgrades before the next wave starts.

You begin with five hearts and five body segments. Enemy contact damages the snake's head and shortens its body, followed by a brief invulnerability period. Hitting a wall or your own body ends the run immediately, regardless of remaining hearts.

The first wave has four enemies. Later waves spawn `3 + 2 × wave` enemies; enemy health increases every two waves and their speed rises each wave.

### Upgrades

| Upgrade | Effect |
| --- | --- |
| Faster Fire | Reduces the shooting interval by 20%, down to a minimum of 0.08 seconds. |
| Extra Heart | Adds one heart to current health. |
| Big Bullet | Adds two pixels to bullet radius and one point of damage. |
| Thick Skin | Adds 0.30 seconds of invulnerability after taking damage. |
| Swift Snake | Reduces the movement interval by 10%, down to a minimum of 0.04 seconds. |
| Piercing Shot | Adds one piercing allowance to new bullets. |

Upgrades can be selected again in later waves and stack for the current run. Restarting resets them.

## Code structure

```text
snake_survivor/
├── main.py                   # Entry point
├── game.py                   # Screens, input, sound, effects, rendering, high score
├── run.py                    # Rules of one run: movement, food, combat, waves, upgrades
├── constants.py              # Colors, dimensions, timings, and balance values
├── utils.py                  # Grid coordinates and food placement helpers
├── entities/
│   ├── snake.py              # Movement, growth, health, and drawing
│   ├── enemy.py              # Pursuit, damage, and drawing
│   ├── bullet.py             # Projectile movement and lifetime
│   └── particle.py           # Visual effects
├── systems/
│   ├── wave_manager.py       # Spawning and wave difficulty
│   ├── upgrade_system.py     # Upgrade definitions and random offers
│   └── sound_manager.py      # WAV generation, playback, and muting
├── ui/
│   ├── screens.py            # Menu, speed selection, pause, and upgrades
│   └── hud.py                # Score, wave, health, and game-over overlay
├── assets/sfx/               # Sound effects generated if missing
└── requirements.txt          # Python dependency
```

A `Run` (`run.py`) holds the rules of one play-through. Callers steer it, call `step(dt)`, and react to the events it returns (shots, hits, food eaten, wave cleared, run over). It has no window, sound, or effects, so tests and the playtest bot drive it directly. `Game` is the app around a run: menu, speed selection, pause, the wave banner and upgrade cards, input, sound, particles, screen shake, and the high score. The snake moves on a discrete grid; enemies and bullets use continuous pixel positions and circular collision checks. Most tuning values live in `constants.py`, while wave scaling lives in `systems/wave_manager.py` and upgrade effects in `Run.pick_upgrade()`. Domain terms are defined in [`GLOSSARY.md`](GLOSSARY.md).

## Playtest bot

`python tools/playtest.py --runs 30 --speed Normal --profile careful` plays full headless runs and prints death causes, waves reached, and upgrade picks. Options: `--profile greedy|careful`, `--upgrades random|first|prefer:<key>`, `--json <path>`.

## Bug reports

Bugs found during review, with root causes, fixes, and regression tests, are in [`docs/bugs/`](docs/bugs/README.md).

## Testing

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Tests run headless (SDL dummy drivers) and cover the snake, wave and upgrade systems, combat, state flow, persistence, and a render smoke test of every screen.

## Current limitations

- Hitting a wall or your own body is instant death regardless of hearts.
- Filling the entire grid is not handled: `random_empty_cell` raises `ValueError` when no cell is free.
- There is no configured linter; the tests do not replace interactive playtesting.
