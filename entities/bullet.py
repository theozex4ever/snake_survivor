from dataclasses import dataclass, field

import pygame

from constants import BULLET_RADIUS, BULLET_COLOR, BULLET_GLOW, SCREEN_WIDTH, SCREEN_HEIGHT


@dataclass
class Bullet:
    pos: pygame.Vector2
    vel: pygame.Vector2
    radius: int = BULLET_RADIUS
    alive: bool = True
    damage: int = 1
    piercing: int = 0
    hit_ids: set = field(default_factory=set)

    def update(self, dt: float) -> None:
        self.pos += self.vel * dt
        if (
            self.pos.x < -50
            or self.pos.x > SCREEN_WIDTH + 50
            or self.pos.y < -50
            or self.pos.y > SCREEN_HEIGHT + 50
        ):
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        glow_r = self.radius + 4
        glow = pygame.Surface((glow_r * 4, glow_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*BULLET_GLOW, 70), (glow_r * 2, glow_r * 2), glow_r)
        surface.blit(glow, (self.pos.x - glow_r * 2, self.pos.y - glow_r * 2))
        pygame.draw.circle(surface, BULLET_COLOR, (int(self.pos.x), int(self.pos.y)), self.radius)
