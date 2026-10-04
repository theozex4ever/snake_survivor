from dataclasses import dataclass
from math import sin

import pygame

from constants import ENEMY_COLOR, ENEMY_OUTLINE, HP_BAR_BG, HP_BAR_FILL


@dataclass
class Enemy:
    pos: pygame.Vector2
    speed: float
    max_hp: int
    hp: int
    radius: int = 13
    alive: bool = True

    def update(self, dt: float, target: pygame.Vector2) -> None:
        if not self.alive:
            return
        delta = target - self.pos
        if delta.length_squared() > 0.0001:
            self.pos += delta.normalize() * self.speed * dt

    def take_damage(self, amount: int) -> bool:
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return

        # Pulsing effect: scale the drawn radius without changing self.radius
        ticks = pygame.time.get_ticks()
        pulse = 0.9 + 0.1 * sin(ticks / 200)
        drawn_radius = int(self.radius * pulse)

        cx, cy = int(self.pos.x), int(self.pos.y)

        pygame.draw.circle(surface, ENEMY_OUTLINE, (cx, cy), drawn_radius + 2)
        pygame.draw.circle(surface, ENEMY_COLOR, (cx, cy), drawn_radius)

        # Inner glow highlight: smaller bright circle offset 2px up-left for a 3D look
        glow_radius = max(1, drawn_radius - 4)
        pygame.draw.circle(surface, (242, 165, 178), (cx - 2, cy - 2), glow_radius)

        eye_offset_x, eye_offset_y = 4, 3
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x - eye_offset_x), int(self.pos.y - eye_offset_y)), 2)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x + eye_offset_x), int(self.pos.y - eye_offset_y)), 2)

        bar_w, bar_h = 28, 5
        bx = self.pos.x - bar_w / 2
        by = self.pos.y - self.radius - 12
        pygame.draw.rect(surface, HP_BAR_BG, (bx, by, bar_w, bar_h), border_radius=2)
        fill_w = bar_w * max(0, self.hp) / self.max_hp
        pygame.draw.rect(surface, HP_BAR_FILL, (bx, by, fill_w, bar_h), border_radius=2)
