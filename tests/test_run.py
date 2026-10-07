import random

import pygame
import pytest

from constants import (
    ENEMY_KILL_SCORE, ENEMY_SPAWN_GAP, FOOD_SCORE, GRID_WIDTH, SCREEN_HEIGHT,
    SCREEN_WIDTH, SPEED_OPTIONS, STARTING_PLAYER_HP,
)
from entities import Bullet, Enemy
from run import (
    EnemyContact, EnemyHit, EnemySpawned, FoodEaten, Run, RunOver, Shot, WaveCleared,
)
from upgrades import offer as make_offer

NORMAL = SPEED_OPTIONS[1][1]
TICK = 0.001  # short enough that the snake doesn't move and no enemy spawns


def enemy_at(run, pos, hp=2):
    e = Enemy(pos=pygame.Vector2(pos), speed=0, max_hp=hp, hp=hp)
    run.enemies.append(e)
    return e


def bullet_at(run, pos, piercing=0):
    b = Bullet(pos=pygame.Vector2(pos), vel=pygame.Vector2(), piercing=piercing)
    run.bullets.append(b)
    return b


def clear_wave(run):
    """Let the wave spawn, kill every enemy, and return the frame's events once it clears."""
    for _ in range(20):
        events = run.step(ENEMY_SPAWN_GAP)
        run.enemies.clear()
        if run.phase == "choosing_upgrade":
            return events
    raise AssertionError("wave never cleared")


def offer(run, *keys):
    """Clear the wave, then pin the offers so a test can pick a specific upgrade."""
    clear_wave(run)
    run.offers = [make_offer(k, run.stats, run.snake.hp) for k in keys]


def wall_bound(run):
    """Put the snake one move from the right wall, heading into it."""
    run.snake.segments = [(GRID_WIDTH - 1, 3), (GRID_WIDTH - 2, 3)]


# --- start -----------------------------------------------------------------

def test_new_run_starts_playing_at_wave_one():
    run = Run(NORMAL, rng=random.Random(0))
    assert run.phase == "playing"
    assert (run.score, run.wave) == (0, 1)
    assert run.snake.alive and run.snake.hp == STARTING_PLAYER_HP
    assert run.food not in run.snake.occupied_cells()
    assert run.time_to_next_move == NORMAL


def test_same_seed_plays_out_identically():
    def play(seed):
        run = Run(NORMAL, rng=random.Random(seed))
        for _ in range(600):
            run.step(1 / 60)
        return run.score, run.food, [tuple(e.pos) for e in run.enemies]

    assert play(7) == play(7)


# --- movement & steering ---------------------------------------------------

def test_snake_moves_once_per_move_interval(run):
    head = run.snake.head
    run.step(run.time_to_next_move - TICK)
    assert run.snake.head == head
    run.step(2 * TICK)
    assert run.snake.head == (head[0] + 1, head[1])


def test_steer_turns_on_next_move(run):
    head = run.snake.head
    run.steer((0, -1))
    run.step(run.time_to_next_move)
    assert run.snake.head == (head[0], head[1] - 1)


def test_steer_is_ignored_when_run_is_over(run):
    wall_bound(run)
    run.step(run.time_to_next_move)
    run.steer((0, 1))
    assert run.snake.direction_queue == []


# --- food ------------------------------------------------------------------

def test_eating_food_scores_grows_and_respawns_food(run):
    head = run.snake.head
    run.food = (head[0] + 1, head[1])
    events = run.step(run.time_to_next_move)
    assert run.score == FOOD_SCORE
    assert run.snake.grow_pending == 1
    assert run.food not in run.snake.occupied_cells()
    assert [e for e in events if isinstance(e, FoodEaten)] == [FoodEaten(run.snake.head_center())]


# --- shooting --------------------------------------------------------------

def until_next_shot(run):
    """Burn the first spawn so the next step's shot sees only the test's enemies."""
    run.step(ENEMY_SPAWN_GAP)
    run.enemies.clear()
    return run.stats.shoot_interval - ENEMY_SPAWN_GAP + TICK


def test_auto_shoot_aims_at_nearest_enemy(run):
    dt = until_next_shot(run)
    head = run.snake.head_center()
    enemy_at(run, head + (300, 0))
    near = enemy_at(run, head + (0, 50))
    shots = [e for e in run.step(dt) if isinstance(e, Shot)]
    assert len(shots) == 1 and len(run.bullets) == 1
    assert shots[0].direction == (near.pos - shots[0].origin).normalize()
    assert run.bullets[0].vel.normalize() == shots[0].direction


def test_no_shot_without_enemies(run):
    events = run.step(until_next_shot(run))
    assert run.bullets == []
    assert not any(isinstance(e, Shot) for e in events)


def test_bullets_carry_current_upgrades(run):
    offer(run, "big_bullet")
    run.pick_upgrade("big_bullet")
    enemy_at(run, run.snake.head_center() + (0, 200))  # nearer than any wave spawn
    run.bullets.clear()
    run.step(run.stats.shoot_interval)
    assert (run.bullets[0].radius, run.bullets[0].damage) == (6, 2)


# --- bullet hits -----------------------------------------------------------

def test_bullet_kill_scores_and_reports_kill(run):
    e = enemy_at(run, (100, 100), hp=1)
    bullet_at(run, (100, 100))
    events = run.step(TICK)
    assert run.score == ENEMY_KILL_SCORE
    assert e not in run.enemies
    assert run.bullets == []
    assert EnemyHit(pygame.Vector2(100, 100), killed=True) in events


def test_non_lethal_hit_reports_hit_and_spends_bullet(run):
    enemy_at(run, (100, 100), hp=5)
    bullet_at(run, (100, 100))
    events = run.step(TICK)
    assert run.bullets == []
    assert EnemyHit(pygame.Vector2(100, 100), killed=False) in events


def test_piercing_bullet_hits_each_enemy_once(run):
    e = enemy_at(run, (100, 100), hp=10)
    bullet_at(run, (100, 100), piercing=1)
    for _ in range(5):  # bullet lingers inside the enemy for several frames
        run.step(TICK)
    assert e.hp == 9
    assert len(run.bullets) == 1


def test_piercing_bullet_still_hits_new_enemy_after_previous_one_dies(run):
    first = enemy_at(run, (100, 100), hp=1)
    bullet = bullet_at(run, (100, 100), piercing=3)
    run.step(TICK)
    assert first not in run.enemies
    del first  # frees the old object so id() could be recycled
    second = enemy_at(run, (100, 100), hp=1)
    run.step(TICK)
    assert second not in run.enemies
    assert bullet.piercing == 1


# --- enemy contact ---------------------------------------------------------

def test_enemy_contact_damages_snake_and_removes_enemy(run):
    head = run.snake.head_center()
    enemy_at(run, head)
    length = len(run.snake.segments)
    events = run.step(TICK)
    assert run.snake.hp == STARTING_PLAYER_HP - 1
    assert len(run.snake.segments) == length - 1
    assert run.enemies == []
    assert EnemyContact(head, head) in events


def test_invulnerable_snake_takes_no_second_hit(run):
    enemy_at(run, run.snake.head_center())
    run.step(TICK)
    enemy_at(run, run.snake.head_center())
    events = run.step(TICK)
    assert run.snake.hp == STARTING_PLAYER_HP - 1
    assert run.enemies == []
    assert any(isinstance(e, EnemyContact) for e in events)


def test_thick_skin_lengthens_invulnerability(run):
    offer(run, "thick_skin")
    run.pick_upgrade("thick_skin")
    enemy_at(run, run.snake.head_center())
    run.step(TICK)
    assert run.snake.invuln_timer == pytest.approx(run.stats.invuln_time)


# --- run over --------------------------------------------------------------

def test_wall_death_ends_run_with_final_score(run):
    run.score = 40
    wall_bound(run)
    events = run.step(run.time_to_next_move)
    assert run.phase == "over"
    assert RunOver(40) in events


def test_lethal_contact_ends_run(run):
    run.snake.hp = 1
    run.score = 90
    enemy_at(run, run.snake.head_center())
    events = run.step(TICK)
    assert run.phase == "over"
    assert RunOver(90) in events


def test_run_over_fires_once_with_simultaneous_lethal_contacts(run):
    run.snake.hp = 1
    for _ in range(3):
        enemy_at(run, run.snake.head_center())
    events = run.step(TICK)
    assert sum(isinstance(e, RunOver) for e in events) == 1


def test_movement_death_freezes_frame_so_score_is_final(run):
    run.score = 40
    wall_bound(run)
    enemy_at(run, (100, 100), hp=1)
    bullet_at(run, (100, 100))
    events = run.step(run.time_to_next_move)
    assert run.score == 40
    assert RunOver(40) in events


def test_finished_run_does_not_advance(run):
    wall_bound(run)
    run.step(run.time_to_next_move)
    enemy_at(run, (100, 100), hp=1)
    bullet_at(run, (100, 100))
    assert run.step(1.0) == []
    assert run.score == 0


# --- waves -----------------------------------------------------------------

def test_wave_spawns_enemies_offscreen_with_spawn_events(run):
    events = run.step(ENEMY_SPAWN_GAP)
    spawned = [e for e in events if isinstance(e, EnemySpawned)]
    assert len(spawned) == 1 and len(run.enemies) == 1
    p = spawned[0].pos
    assert p.x < 0 or p.x > SCREEN_WIDTH or p.y < 0 or p.y > SCREEN_HEIGHT
    assert p is not run.enemies[0].pos  # the event keeps the spawn point as the enemy walks


def test_later_waves_spawn_tougher_enemies(run):
    run.step(ENEMY_SPAWN_GAP)
    first = run.enemies[0]
    for key in ("extra_heart", "extra_heart"):
        offer(run, key)
        run.pick_upgrade(key)
    run.step(ENEMY_SPAWN_GAP)
    third = run.enemies[-1]
    assert third.max_hp == first.max_hp + 1


def test_clearing_a_wave_offers_three_upgrades(run):
    events = clear_wave(run)
    assert WaveCleared(1) in events
    assert len({o.key for o in run.offers}) == 3
    assert all(o.preview for o in run.offers)


def test_offers_preview_the_runs_current_stats_and_hp(run):
    offer(run, "big_bullet")
    run.pick_upgrade("big_bullet")
    run.snake.hp = 2
    clear_wave(run)
    assert run.offers == [make_offer(o.key, run.stats, 2) for o in run.offers]


def test_run_pauses_while_choosing_upgrade(run):
    clear_wave(run)
    head = run.snake.head
    assert run.step(1.0) == []
    assert run.snake.head == head


def test_picking_upgrade_starts_next_wave(run):
    offer(run, "extra_heart", "big_bullet", "thick_skin")
    run.pick_upgrade("extra_heart")
    assert run.phase == "playing"
    assert run.wave == 2
    assert run.offers == []
    assert run.snake.hp == STARTING_PLAYER_HP + 1


def test_picking_an_upgrade_that_was_not_offered_raises(run):
    offer(run, "extra_heart")
    with pytest.raises(ValueError):
        run.pick_upgrade("big_bullet")


def test_picking_an_upgrade_mid_wave_raises(run):
    with pytest.raises(ValueError):
        run.pick_upgrade("extra_heart")

