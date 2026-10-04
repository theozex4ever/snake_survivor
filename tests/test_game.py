"""Game is the adapter around a Run: these tests cover input, screens, effects
and the high score. The rules of a run are tested in test_run.py."""
import pygame

from constants import ENEMY_SPAWN_GAP, GRID_WIDTH, SPEED_OPTIONS, WAVE_BANNER_DURATION
from entities import Bullet, Enemy


def press(game, key):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    game.process_input()


def click(game, pos):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    game.process_input()


def record_sounds(game):
    sounds = []
    game.sound_mgr.play = sounds.append
    return sounds


def enemy_at(game, pos, hp=2):
    e = Enemy(pos=pygame.Vector2(pos), speed=0, max_hp=hp, hp=hp)
    game.run.enemies.append(e)
    return e


def end_run_at_wall(game, score=0):
    game.run.score = score
    game.run.snake.segments = [(GRID_WIDTH - 1, 3), (GRID_WIDTH - 2, 3)]
    game.update(game.run.time_to_next_move)


def clear_wave(game):
    for _ in range(20):
        game.update(ENEMY_SPAWN_GAP)
        game.run.enemies.clear()
        if game.run.phase == "choosing_upgrade":
            return
    raise AssertionError("wave never cleared")


# --- screens & input -------------------------------------------------------

def test_menu_to_speed_select_to_playing(game):
    game.state = "menu"
    press(game, pygame.K_RETURN)
    assert game.state == "speed_select"
    press(game, pygame.K_RIGHT)
    press(game, pygame.K_RETURN)
    assert game.state == "playing"
    assert game.run.move_interval == SPEED_OPTIONS[2][1]


def test_number_key_picks_speed_and_starts(game):
    game.state = "speed_select"
    press(game, pygame.K_4)
    assert game.state == "playing"
    assert game.run.move_interval == SPEED_OPTIONS[3][1]


def test_speed_selection_is_clamped(game):
    game.state = "speed_select"
    game.speed_index = 0
    press(game, pygame.K_LEFT)
    assert game.speed_index == 0


def test_steering_keys_steer_the_run(game):
    press(game, pygame.K_UP)
    assert game.run.snake.direction_queue == [(0, -1)]


def test_mute_toggle(game):
    before = game.sound_mgr.is_muted
    press(game, pygame.K_m)
    assert game.sound_mgr.is_muted != before


def test_pause_and_resume(game):
    press(game, pygame.K_p)
    assert game.state == "paused"
    press(game, pygame.K_ESCAPE)
    assert game.state == "playing"


def test_paused_game_does_not_advance(game):
    press(game, pygame.K_p)
    head = game.run.snake.head
    game.update(1.0)
    assert game.run.snake.head == head


def test_pause_blocked_when_run_is_over(game):
    end_run_at_wall(game)
    press(game, pygame.K_p)
    assert game.state == "playing"


def test_restart_after_run_over_returns_to_menu(game):
    end_run_at_wall(game)
    press(game, pygame.K_r)
    assert game.state == "menu"
    assert game.run is None
    press(game, pygame.K_RETURN)
    press(game, pygame.K_RETURN)
    assert game.run.phase == "playing" and game.run.score == 0


# --- wave banner & upgrade pick --------------------------------------------

def test_wave_banner_shows_before_upgrade_cards(game):
    clear_wave(game)
    press(game, pygame.K_1)
    assert game.run.phase == "choosing_upgrade"  # still on the banner
    game.update(WAVE_BANNER_DURATION)
    press(game, pygame.K_1)
    assert game.run.phase == "playing"
    assert game.run.wave == 2


def test_upgrade_card_click_picks_upgrade(game):
    clear_wave(game)
    game.update(WAVE_BANNER_DURATION)
    game._upgrade_card_rects = [pygame.Rect(0, 0, 100, 100)]
    click(game, (10, 10))
    assert game.run.wave == 2


def test_pause_during_upgrade_pick_returns_to_cards(game):
    clear_wave(game)
    game.update(WAVE_BANNER_DURATION)
    press(game, pygame.K_p)
    assert game.state == "paused"
    press(game, pygame.K_p)
    assert game.state == "playing"
    press(game, pygame.K_2)
    assert game.run.wave == 2


# --- run events → effects --------------------------------------------------

def test_wave_clear_plays_sound(game):
    sounds = record_sounds(game)
    clear_wave(game)
    assert "wave_complete" in sounds


def test_shot_plays_sound_and_spawns_muzzle_particles(game):
    sounds = record_sounds(game)
    enemy_at(game, game.run.snake.head_center() + (0, 200))
    for _ in range(60):
        game.update(1 / 60)
    assert "shoot" in sounds
    assert game.particles


def test_kill_plays_sound_and_shakes(game):
    sounds = record_sounds(game)
    enemy_at(game, (100, 100), hp=1)
    game.run.bullets.append(Bullet(pos=pygame.Vector2(100, 100), vel=pygame.Vector2()))
    game.update(0.001)
    assert sounds == ["kill_enemy"]
    assert game.shake_trauma > 0


def test_enemy_contact_plays_hurt_sound(game):
    sounds = record_sounds(game)
    enemy_at(game, game.run.snake.head_center())
    game.update(0.001)
    assert sounds == ["player_hurt"]


def test_enemy_spawn_shows_telegraph(game):
    game.update(ENEMY_SPAWN_GAP)
    assert len(game._spawn_telegraphs) == 1


def test_run_over_plays_sound_once_and_saves_high_score(game):
    sounds = record_sounds(game)
    game.run.snake.hp = 1
    game.run.score = 90
    for _ in range(3):
        enemy_at(game, game.run.snake.head_center())
    game.update(0.001)
    assert sounds.count("game_over") == 1
    assert game._high_score == 90


def test_wall_death_saves_high_score(game):
    end_run_at_wall(game, score=40)
    assert game._load_high_score() == 40


# --- high score ------------------------------------------------------------

def test_high_score_only_saved_when_beaten(game):
    game._save_high_score(50)
    game._save_high_score(20)
    assert game._load_high_score() == 50


def test_quit_saves_high_score(game):
    game.run.score = 70
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    game.process_input()
    assert not game.running
    assert game._load_high_score() == 70


# --- rendering smoke -------------------------------------------------------

def test_every_screen_renders(game):
    enemy_at(game, game.run.snake.head_center() + (0, 200))
    for _ in range(40):
        game.update(1 / 60)
    for state in ("menu", "speed_select", "playing", "paused"):
        game.state = state
        game.draw()
    game.state = "playing"
    clear_wave(game)
    game.draw()  # wave banner
    game.update(WAVE_BANNER_DURATION)
    game.draw()  # upgrade cards
    assert len(game._upgrade_card_rects) == 3
    press(game, pygame.K_1)
    end_run_at_wall(game)
    game.draw()  # game over
