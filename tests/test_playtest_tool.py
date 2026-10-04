import os
import sys

import pygame

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools"))
import playtest  # noqa: E402

from constants import GRID_WIDTH  # noqa: E402
from entities import Bullet, Enemy  # noqa: E402


def test_wall_death_is_not_counted_as_a_hit(run):
    run.snake.segments = [(GRID_WIDTH - 1, 3), (GRID_WIDTH - 2, 3)]
    run.step(run.time_to_next_move - playtest.DT)  # one move short
    hit, ate = playtest.advance(run)
    assert run.phase == "over"
    assert (hit, ate) == (0, 0)


def test_enemy_contact_death_is_counted_as_a_hit(run):
    run.snake.hp = 1
    run.enemies.append(Enemy(pos=run.snake.head_center(), speed=0, max_hp=1, hp=1))
    hit, _ = playtest.advance(run)
    assert run.phase == "over"
    assert hit == 1


def test_food_counted_when_bullet_kill_scores_in_same_frame(run):
    head = run.snake.head
    run.food = (head[0] + 1, head[1])
    run.step(run.time_to_next_move - playtest.DT)  # the next frame moves onto the food
    run.enemies.append(Enemy(pos=pygame.Vector2(500, 500), speed=0, max_hp=1, hp=1))
    run.bullets.append(Bullet(pos=pygame.Vector2(500, 500), vel=pygame.Vector2()))
    score = run.score
    _, ate = playtest.advance(run)
    assert run.score - score == 30
    assert ate == 1


def test_play_run_completes_and_reports_a_cause():
    result = playtest.play_run(1, "careful", "random", seed=1)
    assert result["cause"] in {"enemy", "wall", "self", "survived"}
    assert result["wave"] >= 1
    assert result["hits"] >= 0 and result["foods"] >= 0


def test_play_run_is_reproducible_from_its_seed():
    assert playtest.play_run(1, "careful", "random", seed=3) == \
        playtest.play_run(1, "careful", "random", seed=3)
