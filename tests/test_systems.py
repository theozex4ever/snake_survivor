import random

import pygame
import pytest

from constants import (
    BASE_ENEMY_HP, ENEMY_SPAWN_GAP, GRID_HEIGHT, GRID_WIDTH,
    SCREEN_HEIGHT, SCREEN_WIDTH,
)
from entities import Bullet, Enemy, Particle
from systems.upgrade_system import UPGRADE_POOL, roll
from systems.wave_manager import WaveManager
from utils import cell_center, clamp, grid_to_pixel, lerp, random_empty_cell


# --- utils -----------------------------------------------------------------

def test_clamp_and_lerp():
    assert clamp(5, 0, 3) == 3
    assert clamp(-1, 0, 3) == 0
    assert lerp(0, 10, 0.25) == 2.5


def test_grid_conversions():
    assert grid_to_pixel((2, 3)) == (44, 66)
    assert cell_center((0, 0)) == pygame.Vector2(11, 11)


def test_random_empty_cell_avoids_occupied():
    occupied = {(x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)}
    occupied.remove((7, 9))
    assert random_empty_cell(occupied) == (7, 9)


def test_random_empty_cell_full_grid_raises():
    occupied = {(x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)}
    with pytest.raises(ValueError):
        random_empty_cell(occupied)


# --- wave manager ----------------------------------------------------------

def spawn_wave(wm):
    """Run the spawn clock until the wave has spawned everything; return the enemies."""
    enemies = []
    for _ in range(100):
        enemy, _ = wm.update(ENEMY_SPAWN_GAP, living_count=len(enemies))
        if enemy is not None:
            enemies.append(enemy)
    return enemies


def test_wave_spawns_four_then_completes():
    wm = WaveManager(random.Random(0))
    assert len(spawn_wave(wm)) == 4
    assert wm.update(0.0, living_count=0) == (None, True)


def test_wave_not_complete_while_enemies_alive():
    wm = WaveManager(random.Random(0))
    spawn_wave(wm)
    assert wm.update(0.1, living_count=2) == (None, False)


def test_advance_scales_enemy_count_and_hp():
    wm = WaveManager(random.Random(0))
    assert {e.max_hp for e in spawn_wave(wm)} == {BASE_ENEMY_HP}
    wm.advance()
    assert wm.wave == 2
    wave_two = spawn_wave(wm)
    assert len(wave_two) == 3 + 2 * 2
    assert {e.max_hp for e in wave_two} == {BASE_ENEMY_HP}
    wm.advance()
    assert {e.max_hp for e in spawn_wave(wm)} == {BASE_ENEMY_HP + 1}


def test_enemy_speed_rises_per_wave():
    wm = WaveManager(random.Random(0))
    first = [e.speed for e in spawn_wave(wm)]
    for _ in range(5):
        wm.advance()
    later = [e.speed for e in spawn_wave(wm)]
    assert min(later) > max(first)


def test_spawn_positions_are_offscreen():
    wm = WaveManager(random.Random(0))
    for _ in range(25):
        for e in spawn_wave(wm):
            p = e.pos
            assert p.x < 0 or p.x > SCREEN_WIDTH or p.y < 0 or p.y > SCREEN_HEIGHT
        wm.advance()


# --- upgrades --------------------------------------------------------------

def test_roll_offers_three_distinct_upgrades():
    rng = random.Random(0)
    for _ in range(50):
        offers = roll(rng=rng)
        assert len(offers) == 3
        assert len({o["key"] for o in offers}) == 3


def test_every_upgrade_has_required_fields():
    for u in UPGRADE_POOL:
        assert {"key", "name", "desc", "stat"} <= u.keys()


# --- entities --------------------------------------------------------------

def test_enemy_moves_toward_target():
    e = Enemy(pos=pygame.Vector2(0, 0), speed=100, max_hp=2, hp=2)
    e.update(0.5, pygame.Vector2(100, 0))
    assert e.pos == pygame.Vector2(50, 0)


def test_enemy_take_damage_reports_death():
    e = Enemy(pos=pygame.Vector2(), speed=1, max_hp=2, hp=2)
    assert e.take_damage(1) is False
    assert e.take_damage(1) is True
    assert not e.alive


def test_bullet_moves_and_expires_offscreen():
    b = Bullet(pos=pygame.Vector2(10, 10), vel=pygame.Vector2(100, 0))
    b.update(0.1)
    assert b.pos == pygame.Vector2(20, 10)
    b.pos = pygame.Vector2(SCREEN_WIDTH + 51, 10)
    b.update(0.0)
    assert not b.alive


def test_particle_expires():
    p = Particle(pos=pygame.Vector2(), vel=pygame.Vector2(10, 0),
                 color=(1, 2, 3), life=0.1, max_life=0.1, radius=3)
    p.update(0.2)
    assert not p.alive
