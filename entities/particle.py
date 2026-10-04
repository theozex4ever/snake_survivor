from dataclasses import dataclass
from typing import Tuple

import pygame


@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    color: Tuple[int, int, int]
    life: float
    max_life: float
    radius: float

    @property
    def alive(self) -> bool:
        return self.life > 0

    def update(self, dt: float) -> None:
        self.life -= dt
        self.pos += self.vel * dt
        self.vel *= 0.97
        self.radius *= 0.985

    def draw(self, surface: pygame.Surface) -> None:
        if self.life <= 0:
            return
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        r = max(1, int(self.radius))
        temp = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(temp, (*self.color, alpha), (r * 2, r * 2), r)
        surface.blit(temp, (self.pos.x - r * 2, self.pos.y - r * 2))
