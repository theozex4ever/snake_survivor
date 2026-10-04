import random

import pygame

from constants import (
    ENEMY_SPAWN_GAP, BASE_ENEMY_HP, BASE_ENEMY_SPEED,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)


class WaveManager:
    def __init__(self) -> None:
        self.wave: int = 1
        self.enemies_to_spawn: int = 4
        self.enemies_spawned_in_wave: int = 0
        self.spawn_timer: float = 0.0

    def reset(self) -> None:
        self.wave = 1
        self.enemies_to_spawn = 4
        self.enemies_spawned_in_wave = 0
        self.spawn_timer = 0.0

    def update(self, dt: float, living_count: int) -> str:
        """Returns 'spawn', 'wave_complete', or '' each frame."""
        self.spawn_timer += dt
        if self.enemies_spawned_in_wave < self.enemies_to_spawn:
            if self.spawn_timer >= ENEMY_SPAWN_GAP:
                self.spawn_timer = 0.0
                self.enemies_spawned_in_wave += 1
                return "spawn"
        elif living_count == 0:
            return "wave_complete"
        return ""

    def advance(self) -> None:
        self.wave += 1
        self.enemies_to_spawn = 3 + self.wave * 2
        self.enemies_spawned_in_wave = 0
        self.spawn_timer = 0.0

    def enemy_hp(self) -> int:
        return BASE_ENEMY_HP + (self.wave - 1) // 2

    def enemy_speed(self) -> float:
        return BASE_ENEMY_SPEED + (self.wave - 1) * 6.5 + random.uniform(-6, 8)

    def random_spawn_pos(self) -> pygame.Vector2:
        side = random.randint(0, 3)
        margin = 40
        if side == 0:
            return pygame.Vector2(random.randint(0, SCREEN_WIDTH), -margin)
        elif side == 1:
            return pygame.Vector2(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + margin)
        elif side == 2:
            return pygame.Vector2(-margin, random.randint(0, SCREEN_HEIGHT))
        else:
            return pygame.Vector2(SCREEN_WIDTH + margin, random.randint(0, SCREEN_HEIGHT))
