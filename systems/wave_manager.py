import random
from typing import Optional, Tuple

import pygame

from constants import (
    ENEMY_SPAWN_GAP, BASE_ENEMY_HP, BASE_ENEMY_SPEED,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)
from entities import Enemy


class WaveManager:
    def __init__(self, rng: random.Random = random) -> None:
        self.rng = rng
        self.wave: int = 1
        self.enemies_to_spawn: int = 4
        self.enemies_spawned_in_wave: int = 0
        self.spawn_timer: float = 0.0

    def update(self, dt: float, living_count: int) -> Tuple[Optional[Enemy], bool]:
        """Advance the spawn clock; return (enemy to spawn or None, whether the wave is complete)."""
        self.spawn_timer += dt
        if self.enemies_spawned_in_wave < self.enemies_to_spawn:
            if self.spawn_timer >= ENEMY_SPAWN_GAP:
                self.spawn_timer = 0.0
                self.enemies_spawned_in_wave += 1
                return self._spawn(), False
            return None, False
        return None, living_count == 0

    def advance(self) -> None:
        self.wave += 1
        self.enemies_to_spawn = 3 + self.wave * 2
        self.enemies_spawned_in_wave = 0
        self.spawn_timer = 0.0

    def _spawn(self) -> Enemy:
        hp = BASE_ENEMY_HP + (self.wave - 1) // 2
        speed = BASE_ENEMY_SPEED + (self.wave - 1) * 6.5 + self.rng.uniform(-6, 8)
        return Enemy(pos=self._spawn_pos(), speed=speed, max_hp=hp, hp=hp)

    def _spawn_pos(self) -> pygame.Vector2:
        side = self.rng.randint(0, 3)
        margin = 40
        if side == 0:
            return pygame.Vector2(self.rng.randint(0, SCREEN_WIDTH), -margin)
        elif side == 1:
            return pygame.Vector2(self.rng.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + margin)
        elif side == 2:
            return pygame.Vector2(-margin, self.rng.randint(0, SCREEN_HEIGHT))
        else:
            return pygame.Vector2(SCREEN_WIDTH + margin, self.rng.randint(0, SCREEN_HEIGHT))
