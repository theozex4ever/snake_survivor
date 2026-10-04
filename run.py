"""The rules of one run: steering, food, auto-fire, waves, upgrades and death.

Run knows nothing about the window, input devices, sound or effects. Its
caller steers it, steps it, and reacts to the events each step returns.
"""
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

from constants import (
    AUTO_SHOOT_INTERVAL, BULLET_RADIUS, BULLET_SPEED, ENEMY_KILL_SCORE,
    ENEMY_TOUCH_DAMAGE, FOOD_SCORE, INVULN_TIME, PLAYER_COLLISION_RADIUS,
)
from entities import Bullet, Enemy, Snake
from systems.upgrade_system import roll as roll_upgrades
from systems.wave_manager import WaveManager
from utils import random_empty_cell


# --- events ----------------------------------------------------------------

@dataclass(frozen=True)
class Shot:
    origin: pygame.Vector2
    direction: pygame.Vector2


@dataclass(frozen=True)
class FoodEaten:
    pos: pygame.Vector2


@dataclass(frozen=True)
class EnemyHit:
    pos: pygame.Vector2
    killed: bool


@dataclass(frozen=True)
class EnemyContact:
    """An enemy reached the snake's head and burst; it costs HP unless the snake is invulnerable."""
    head_pos: pygame.Vector2
    enemy_pos: pygame.Vector2


@dataclass(frozen=True)
class EnemySpawned:
    pos: pygame.Vector2


@dataclass(frozen=True)
class WaveCleared:
    wave: int


@dataclass(frozen=True)
class RunOver:
    score: int


# --- run -------------------------------------------------------------------

class Run:
    """One play-through.

    Phases: "playing" -> "choosing_upgrade" -> "playing" ... -> "over".
    step() only advances while playing, steer() only queues turns while
    playing, and pick_upgrade() is only valid while choosing an upgrade.
    RunOver is emitted exactly once, and the score is final when it is.
    """

    def __init__(self, move_interval: float, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()
        self.phase = "playing"
        self.snake = Snake()
        self.score = 0
        self.bullets: List[Bullet] = []
        self.enemies: List[Enemy] = []
        self.offered_upgrades: List[dict] = []

        # Per-run stats that upgrades change.
        self.move_interval = move_interval
        self.shoot_interval = AUTO_SHOOT_INTERVAL
        self.bullet_speed = BULLET_SPEED
        self.bullet_radius = BULLET_RADIUS
        self.bullet_damage = 1
        self.bullet_piercing = 0
        self.invuln_time = INVULN_TIME

        self._move_timer = 0.0
        self._shoot_timer = 0.0
        self._waves = WaveManager(self.rng)
        self.food = self._spawn_food()

    @property
    def wave(self) -> int:
        return self._waves.wave

    @property
    def time_to_next_move(self) -> float:
        return self.move_interval - self._move_timer

    def steer(self, direction: Tuple[int, int]) -> None:
        if self.phase == "playing":
            self.snake.set_direction(direction)

    def pick_upgrade(self, key: str) -> None:
        if self.phase != "choosing_upgrade":
            raise ValueError(f"can't pick an upgrade while {self.phase}")
        if key not in [u["key"] for u in self.offered_upgrades]:
            raise ValueError(f"upgrade {key!r} was not offered")

        if key == "faster_fire":
            self.shoot_interval = max(0.08, self.shoot_interval * 0.80)
        elif key == "extra_heart":
            self.snake.hp += 1
        elif key == "big_bullet":
            self.bullet_radius += 2
            self.bullet_damage += 1
        elif key == "thick_skin":
            self.invuln_time += 0.30
        elif key == "swift_snake":
            self.move_interval = max(0.04, self.move_interval * 0.90)
        elif key == "piercing_shot":
            self.bullet_piercing += 1

        self.offered_upgrades = []
        self._waves.advance()
        self.phase = "playing"

    def step(self, dt: float) -> list:
        if self.phase != "playing":
            return []
        events: list = []

        self.snake.update(dt)
        self._move_timer += dt
        self._shoot_timer += dt

        if self._move_timer >= self.move_interval:
            self._move_timer -= self.move_interval
            self.snake.move()
            if not self.snake.alive:
                # End before anything else scores, so RunOver carries the final score.
                return events + self._end()
            if self.snake.head == self.food:
                self.snake.grow(1)
                self.score += FOOD_SCORE
                events.append(FoodEaten(self.snake.head_center()))
                self.food = self._spawn_food()

        living_count = sum(1 for e in self.enemies if e.alive)
        enemy, wave_complete = self._waves.update(dt, living_count)
        if enemy is not None:
            self.enemies.append(enemy)
            events.append(EnemySpawned(pygame.Vector2(enemy.pos)))
        elif wave_complete:
            self.offered_upgrades = roll_upgrades(rng=self.rng)
            self.phase = "choosing_upgrade"
            events.append(WaveCleared(self.wave))

        if self._shoot_timer >= self.shoot_interval:
            self._shoot_timer -= self.shoot_interval
            events += self._auto_shoot()

        head_pos = self.snake.head_center()
        for e in self.enemies:
            e.update(dt, head_pos)
        for b in self.bullets:
            b.update(dt)

        events += self._resolve_bullet_hits()
        events += self._resolve_enemy_contact(head_pos)

        self.bullets = [b for b in self.bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        return events

    # ------------------------------------------------------------------

    def _spawn_food(self) -> Tuple[int, int]:
        return random_empty_cell(self.snake.occupied_cells(), self.rng)

    def _end(self) -> list:
        self.phase = "over"
        return [RunOver(self.score)]

    def _auto_shoot(self) -> list:
        living = [e for e in self.enemies if e.alive]
        if not living:
            return []
        origin = self.snake.head_center()
        target = min(living, key=lambda e: (e.pos - origin).length_squared())
        delta = target.pos - origin
        if delta.length_squared() < 0.001:
            return []
        direction = delta.normalize()
        self.bullets.append(Bullet(
            pos=origin.copy(),
            vel=direction * self.bullet_speed,
            radius=self.bullet_radius,
            damage=self.bullet_damage,
            piercing=self.bullet_piercing,
        ))
        return [Shot(origin, direction)]

    def _resolve_bullet_hits(self) -> list:
        events = []
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive or enemy.uid in bullet.hit_ids:
                    continue
                combined = bullet.radius + enemy.radius
                if (bullet.pos - enemy.pos).length_squared() <= combined * combined:
                    bullet.hit_ids.add(enemy.uid)
                    killed = enemy.take_damage(bullet.damage)
                    if killed:
                        self.score += ENEMY_KILL_SCORE
                    events.append(EnemyHit(pygame.Vector2(enemy.pos), killed))
                    if bullet.piercing > 0:
                        bullet.piercing -= 1
                    else:
                        bullet.alive = False
                    break
        return events

    def _resolve_enemy_contact(self, head_pos: pygame.Vector2) -> list:
        events = []
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            combined = enemy.radius + PLAYER_COLLISION_RADIUS
            if (enemy.pos - head_pos).length_squared() <= combined * combined:
                enemy.alive = False
                self.snake.take_damage(ENEMY_TOUCH_DAMAGE, self.invuln_time)
                events.append(EnemyContact(pygame.Vector2(head_pos), pygame.Vector2(enemy.pos)))
                if not self.snake.alive:
                    return events + self._end()
        return events
