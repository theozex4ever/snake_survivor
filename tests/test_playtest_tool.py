import os
import sys

import pygame

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools"))
import playtest  # noqa: E402

from constants import GRID_WIDTH  # noqa: E402
from entities import Bullet, Enemy  # noqa: E402


def test_wall_death_is_not_counted_as_a_hit(game):
    game.snake.segments = [(GRID_WIDTH - 1, 3), (GRID_WIDTH - 2, 3)]
    game.update(game.move_interval - playtest.DT)  # one move short
    hit, ate = playtest.advance(game)
    assert not game.snake.alive
    assert (hit, ate) == (0, 0)


def test_enemy_contact_death_is_counted_as_a_hit(game):
    game.snake.hp = 1
    game.enemies.append(Enemy(pos=game.snake.head_center(), speed=0, max_hp=1, hp=1))
    hit, _ = playtest.advance(game)
    assert not game.snake.alive
    assert hit == 1


def test_food_counted_when_bullet_kill_scores_in_same_frame(game):
    head = game.snake.head
    game.food = (head[0] + 1, head[1])
    game.move_timer = game.move_interval
    game.enemies.append(Enemy(pos=pygame.Vector2(500, 500), speed=0, max_hp=1, hp=1))
    game.bullets.append(Bullet(pos=pygame.Vector2(500, 500), vel=pygame.Vector2()))
    score = game.score
    _, ate = playtest.advance(game)
    assert game.score - score == 30
    assert ate == 1


def test_play_run_completes_and_reports_a_cause(game):
    import random
    random.seed(1)
    result = playtest.play_run(game, 1, "careful", "random", random.Random(1))
    assert result["cause"] in {"enemy", "wall", "self", "survived"}
    assert result["wave"] >= 1
    assert result["hits"] >= 0 and result["foods"] >= 0
