# Bug Tracker

Bugs found in Snake Survivor, split by the kind of QA that catches them. Each has a root cause, fix, and verification.

**Scope:** only report bugs that exist on the current branch. Reproduce on that branch's code before filing, record it in the report's `Branch` field, and don't file bugs found only on other branches or in code that isn't checked out. Scope is the checked-out code, not just the branch's diff against `main`: a bug is reportable if it reproduces on the branch, whoever introduced it. All current reports were found on `docs/setup-agent-skills`.

**Two tracks:**

| Track | What it is | Typical finder | Template |
| --- | --- | --- | --- |
| [Technical](technical/) (`TECH-`) | Software defects: logic errors, missed state transitions, persistence, hangs, robustness. The player may never notice. | Code review, unit and integration tests, static reading | [technical/TEMPLATE.md](technical/TEMPLATE.md) |
| [Gameplay](gameplay/) (`GP-`) | What the player experiences: controls, fairness, feel, balance, whether a feature works as promised. | Playtesting, play-feel analysis | [gameplay/TEMPLATE.md](gameplay/TEMPLATE.md) |

A bug goes in the track of its *symptom*. If one root cause shows up as both, file one report per symptom and cross-link them.

**Review-found bugs:** TECH-005 to TECH-008 were found in review of PR #2 and are defects in the fixes made for earlier reports. They are recorded because the first round of tests missed them.

**Honesty note:** GP-001 to GP-004 and all technical bugs were found by code review and confirmed with tests. GP-005 to GP-007 were found by the headless bot in `tools/playtest.py`, which is a simulation, not a human. See the [playtest baseline](playtests/2026-10-04-baseline.md) for method, limits, and raw numbers. GP-008 to GP-010 came from hands-on human play on `refactor/improve-codebase-architecture`. GP-009 and GP-010 were reproduced on that branch; GP-008 was not, and is kept as an informative record.

**Method (technical and GP-001 to GP-004):** read the code, then wrote tests. All new tests were run against the original commit (`3b375eb`) before the fixes, so the "Failing test" column is evidence that the bug existed. Tests that merely depend on new internals are not counted.

## Gameplay bugs

| ID | Title | Severity | Area | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| [GP-001](gameplay/GP-001-dropped-turn-inputs.md) | Quick turn combos drop the first input | Medium | Controls | Fixed | `test_turns_are_buffered_across_moves` |
| [GP-002](gameplay/GP-002-tail-cell-collision.md) | Moving into the vacating tail cell kills the snake | Medium | Movement | Fixed | `test_moving_into_vacating_tail_is_safe` |
| [GP-003](gameplay/GP-003-piercing-rehits-enemy.md) | Piercing Shot upgrade wastes its pierce on one enemy | High | Combat / upgrades | Fixed | `test_piercing_bullet_hits_each_enemy_once` |
| [GP-004](gameplay/GP-004-pause-while-dead.md) | Game can be paused after death | Low | UX | Fixed | `test_pause_blocked_when_dead` |
| [GP-005](gameplay/GP-005-big-bullet-dominates.md) | Big Bullet dominates every other upgrade | Medium | Balance | Open | Found by bot playtest (see [baseline](playtests/2026-10-04-baseline.md)) |
| [GP-006](gameplay/GP-006-runs-end-by-hp-attrition.md) | Every run is decided by a fixed hit budget | Medium | Balance | Open | Found by bot playtest |
| [GP-007](gameplay/GP-007-four-upgrades-do-not-help.md) | Four upgrades give no measurable benefit | Medium | Balance | Open | Found by bot playtest |
| [GP-008](gameplay/GP-008-no-food-not-reproduced.md) | "No food in the game" (not reproduced) | n/a | UX | Informative | Not reproduced; findings only |
| [GP-009](gameplay/GP-009-black-squares-on-alpha-windows.md) | Black squares behind the hearts and food on the upgrade screen | Medium | Rendering | Fixed | `test_frames_are_opaque_on_windows_with_an_alpha_channel` |
| [GP-010](gameplay/GP-010-arrow-glyphs-render-as-boxes.md) | Arrows in the upgrade previews render as boxes | Low | UX | Fixed | `test_every_rendered_character_has_a_glyph` |

## Technical bugs

| ID | Title | Severity | Area | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| [TECH-001](technical/TECH-001-enemy-death-skips-game-over.md) | Enemy kill skips game-over handling (sound, high-score save) | High | Game flow | Fixed | `test_lethal_contact_saves_high_score` |
| [TECH-002](technical/TECH-002-high-score-lost-on-window-close.md) | High score lost when closing the window | Medium | Persistence | Fixed | `test_quit_saves_high_score`, `test_wall_death_saves_high_score` |
| [TECH-003](technical/TECH-003-food-placement-hang.md) | Food placement loops forever on a full grid | Low | Utils | Fixed | `test_random_empty_cell_full_grid_raises` (hangs) |
| [TECH-004](technical/TECH-004-frame-spike-skips-simulation.md) | Frame-time spikes skip moves and collisions | Low | Main loop | Fixed | Not covered by an automated test |
| [TECH-005](technical/TECH-005-piercing-hit-id-reuse.md) | Piercing bullets track enemies by recyclable `id()` | Medium | Combat | Fixed | Found in PR review of the GP-003 fix |
| [TECH-006](technical/TECH-006-game-over-fires-per-contact.md) | Game-over handling fires once per overlapping enemy | Medium | Game flow | Fixed | Found in PR review of the TECH-001 fix |
| [TECH-007](technical/TECH-007-score-changes-after-death-save.md) | Score keeps changing after the death save | Medium | Persistence | Fixed | Found in PR review of the TECH-002 fix |
| [TECH-008](technical/TECH-008-playtest-bot-miscounts.md) | Playtest bot miscounted hits and food | Low | Tooling | Fixed | Found in PR review |

**Severity:** High = wrong outcome in normal play. Medium = noticeably unfair or data loss. Low = edge case or polish.

## Not bugs, but worth deciding
- Walls are instant death regardless of hearts.

