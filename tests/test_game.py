import pygame

import game as game_module
from constants import (
    ENEMY_KILL_SCORE, FOOD_SCORE, GRID_WIDTH, SPEED_OPTIONS, STARTING_PLAYER_HP,
    WAVE_BANNER_DURATION,
)
from entities import Bullet, Enemy


def press(game, key):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    game.process_input()


def enemy_at(game, pos, hp=2):
    e = Enemy(pos=pygame.Vector2(pos), speed=0, max_hp=hp, hp=hp)
    game.enemies.append(e)
    return e


# --- state flow ------------------------------------------------------------

def test_menu_to_speed_select_to_playing(game):
    game.state = "menu"
    press(game, pygame.K_RETURN)
    assert game.state == "speed_select"
    press(game, pygame.K_RIGHT)
    press(game, pygame.K_RETURN)
    assert game.state == "playing"
    assert game.move_interval == SPEED_OPTIONS[2][1]


def test_number_key_picks_speed_and_starts(game):
    game.state = "speed_select"
    press(game, pygame.K_4)
    assert game.state == "playing"
    assert game.move_interval == SPEED_OPTIONS[3][1]


def test_speed_selection_is_clamped(game):
    game.state = "speed_select"
    game.speed_index = 0
    press(game, pygame.K_LEFT)
    assert game.speed_index == 0


def test_pause_and_resume(game):
    press(game, pygame.K_p)
    assert game.state == "paused"
    press(game, pygame.K_ESCAPE)
    assert game.state == "playing"


def test_pause_blocked_when_dead(game):
    game.snake.alive = False
    press(game, pygame.K_p)
    assert game.state == "playing"


def test_paused_game_does_not_advance(game):
    game.state = "paused"
    head = game.snake.head
    game.update(1.0)
    assert game.snake.head == head


def test_steering_keys(game):
    press(game, pygame.K_UP)
    assert game.snake.direction_queue == [(0, -1)]


def test_mute_toggle(game):
    muted = game.sound_mgr.muted if hasattr(game.sound_mgr, "muted") else None
    press(game, pygame.K_m)
    if muted is not None:
        assert game.sound_mgr.muted != muted


# --- food & scoring --------------------------------------------------------

def test_eating_food_scores_and_grows(game):
    head = game.snake.head
    game.food = (head[0] + 1, head[1])
    game.update(game.move_interval)
    assert game.score == FOOD_SCORE
    assert game.snake.grow_pending == 1
    assert game.food != game.snake.head


def test_food_never_spawns_on_snake(game):
    for _ in range(200):
        assert game.spawn_food() not in game.snake.occupied_cells()


# --- combat ----------------------------------------------------------------

def test_nearest_enemy_selected(game):
    head = game.snake.head_center()
    far = enemy_at(game, head + (300, 0))
    near = enemy_at(game, head + (50, 0))
    assert game.nearest_enemy() is near
    assert far in game.enemies


def test_auto_shoot_aims_at_enemy(game):
    head = game.snake.head_center()
    enemy_at(game, head + (200, 0))
    game.auto_shoot()
    assert len(game.bullets) == 1
    assert game.bullets[0].vel.normalize() == pygame.Vector2(1, 0)


def test_no_shot_without_enemies(game):
    game.auto_shoot()
    assert game.bullets == []


def test_bullet_kill_scores(game):
    e = enemy_at(game, (100, 100), hp=1)
    game.bullets.append(Bullet(pos=pygame.Vector2(100, 100), vel=pygame.Vector2()))
    game.wave_mgr.enemies_spawned_in_wave = 0
    game.update(0.001)
    assert game.score == ENEMY_KILL_SCORE
    assert e not in game.enemies
    assert game.bullets == []


def test_non_piercing_bullet_dies_on_hit(game):
    enemy_at(game, (100, 100), hp=5)
    game.bullets.append(Bullet(pos=pygame.Vector2(100, 100), vel=pygame.Vector2()))
    game.update(0.001)
    assert game.bullets == []


def test_piercing_bullet_hits_each_enemy_once(game):
    e = enemy_at(game, (100, 100), hp=10)
    game.bullets.append(Bullet(pos=pygame.Vector2(100, 100), vel=pygame.Vector2(),
                               piercing=1))
    for _ in range(5):  # bullet lingers inside the enemy for several frames
        game.update(0.001)
    assert e.hp == 9
    assert len(game.bullets) == 1


def test_enemy_contact_damages_snake_and_removes_enemy(game):
    enemy_at(game, game.snake.head_center())
    length = len(game.snake.segments)
    game.update(0.001)
    assert game.snake.hp == STARTING_PLAYER_HP - 1
    assert len(game.snake.segments) == length - 1
    assert game.enemies == []


def test_invulnerable_snake_takes_no_second_hit(game):
    enemy_at(game, game.snake.head_center())
    game.update(0.001)
    enemy_at(game, game.snake.head_center())
    game.update(0.001)
    assert game.snake.hp == STARTING_PLAYER_HP - 1


def test_lethal_contact_saves_high_score(game):
    game.snake.hp = 1
    game.score = 90
    enemy_at(game, game.snake.head_center())
    game.update(0.001)
    assert not game.snake.alive
    assert game._high_score == 90


def test_wall_death_saves_high_score(game):
    game.score = 40
    game.snake.segments = [(GRID_WIDTH - 1, 3), (GRID_WIDTH - 2, 3)]
    game.update(game.move_interval)
    assert not game.snake.alive
    assert game._high_score == 40


# --- waves & upgrades ------------------------------------------------------

def test_wave_clear_then_upgrade_pick(game):
    game.wave_mgr.enemies_spawned_in_wave = game.wave_mgr.enemies_to_spawn
    game.update(0.001)
    assert game.state == "wave_clear"
    game.update(WAVE_BANNER_DURATION + 0.1)
    assert game.state == "upgrade_pick"
    assert len(game.offered_upgrades) == 3


def test_picking_upgrade_starts_next_wave(game):
    game.state = "upgrade_pick"
    game.offered_upgrades = [{"key": "extra_heart"}, {"key": "big_bullet"}, {"key": "thick_skin"}]
    press(game, pygame.K_1)
    assert game.state == "playing"
    assert game.wave_mgr.wave == 2
    assert game.snake.hp == STARTING_PLAYER_HP + 1


def test_upgrade_effects(game):
    game._apply_upgrade("faster_fire")
    assert abs(game.shoot_interval - 0.48) < 1e-9
    game._apply_upgrade("big_bullet")
    assert (game.bullet_radius, game.bullet_damage) == (6, 2)
    game._apply_upgrade("thick_skin")
    assert abs(game.invuln_time - 1.05) < 1e-9
    game._apply_upgrade("piercing_shot")
    assert game.bullet_piercing == 1
    before = game.move_interval
    game._apply_upgrade("swift_snake")
    assert abs(game.move_interval - before * 0.9) < 1e-9


def test_upgrade_floors(game):
    game.shoot_interval = 0.08
    game.move_interval = 0.04
    game._apply_upgrade("faster_fire")
    game._apply_upgrade("swift_snake")
    assert game.shoot_interval == 0.08
    assert game.move_interval == 0.04


def test_upgrade_card_click(game):
    game.state = "upgrade_pick"
    game.offered_upgrades = [{"key": "piercing_shot"}]
    game._upgrade_card_rects = [pygame.Rect(0, 0, 100, 100)]
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 10), button=1))
    game.process_input()
    assert game.bullet_piercing == 1


def test_reset_clears_run_state(game):
    game._apply_upgrade("big_bullet")
    game.score = 99
    game.reset()
    assert game.score == 0
    assert game.bullet_damage == 1
    assert game.wave_mgr.wave == 1


# --- persistence -----------------------------------------------------------

def test_high_score_only_saved_when_beaten(game, tmp_path):
    game.score = 50
    game._save_high_score()
    game.score = 20
    game._save_high_score()
    assert game._load_high_score() == 50


def test_quit_saves_high_score(game):
    game.score = 70
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    game.process_input()
    assert not game.running
    assert game._load_high_score() == 70


def test_restart_after_death_returns_to_menu(game):
    game.snake.alive = False
    press(game, pygame.K_r)
    assert game.state == "menu"
    assert game.snake.alive


# --- rendering smoke -------------------------------------------------------

def test_every_state_renders(game):
    enemy_at(game, (300, 300))
    game.auto_shoot()
    game.offered_upgrades = game_module.roll_upgrades()
    for state in ("menu", "speed_select", "playing", "paused", "wave_clear", "upgrade_pick"):
        game.state = state
        game.draw()
    game.snake.alive = False
    game.state = "playing"
    game.draw()
