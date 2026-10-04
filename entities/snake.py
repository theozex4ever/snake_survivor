from typing import List, Tuple

import pygame

from constants import (
    GRID_WIDTH, GRID_HEIGHT, CELL_SIZE,
    INITIAL_SNAKE_LENGTH, STARTING_PLAYER_HP, INVULN_TIME,
    SNAKE_HEAD_COLOR, SNAKE_BODY_COLOR, SNAKE_OUTLINE,
)
from utils import grid_to_pixel, cell_center


class Snake:
    def __init__(self) -> None:
        cx = GRID_WIDTH // 2
        cy = GRID_HEIGHT // 2
        self.segments: List[Tuple[int, int]] = [(cx - i, cy) for i in range(INITIAL_SNAKE_LENGTH)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.grow_pending = 0
        self.alive = True
        self.hp = STARTING_PLAYER_HP
        self.invuln_timer = 0.0

    @property
    def head(self) -> Tuple[int, int]:
        return self.segments[0]

    def occupied_cells(self) -> set:
        return set(self.segments)

    def head_center(self) -> pygame.Vector2:
        return cell_center(self.head)

    def set_direction(self, direction: Tuple[int, int]) -> None:
        dx, dy = direction
        cdx, cdy = self.direction
        if (dx, dy) == (-cdx, -cdy):
            return
        self.next_direction = direction

    def move(self) -> None:
        if not self.alive:
            return
        self.direction = self.next_direction
        hx, hy = self.head
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)
        if not (0 <= new_head[0] < GRID_WIDTH and 0 <= new_head[1] < GRID_HEIGHT):
            self.alive = False
            return
        if new_head in self.segments:
            self.alive = False
            return
        self.segments.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.segments.pop()

    def grow(self, amount: int = 1) -> None:
        self.grow_pending += amount

    def update(self, dt: float) -> None:
        if self.invuln_timer > 0:
            self.invuln_timer -= dt

    def can_take_damage(self) -> bool:
        return self.invuln_timer <= 0 and self.alive

    def take_damage(self, amount: int = 1, invuln_time: float = INVULN_TIME) -> None:
        if not self.can_take_damage():
            return
        self.hp -= amount
        self.invuln_timer = invuln_time
        shrink = min(amount, max(0, len(self.segments) - 1))
        for _ in range(shrink):
            if len(self.segments) > 1:
                self.segments.pop()
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        blink = self.invuln_timer > 0 and int(self.invuln_timer * 12) % 2 == 0
        n = len(self.segments)

        # Draw body segments from tail to head (reversed list: index 0 = tail, index n-1 = head)
        for i, seg in enumerate(self.segments[::-1]):
            px, py = grid_to_pixel(seg)
            is_head = (i == n - 1)
            is_tail = (i == 0)

            if is_head:
                inset = 2
                base_color = SNAKE_HEAD_COLOR
            elif is_tail:
                inset = 4  # more inset = tapered look
                # tail is fully darkened (factor at i=0 in forward order = n-1 in reversed)
                factor = 1.0 - 0.35 * ((n - 1) / max(1, n - 1))  # == 0.65
                base_color = tuple(int(c * factor) for c in SNAKE_BODY_COLOR)
            else:
                inset = 3
                # i here is reversed index; forward index = (n - 1 - i)
                forward_i = n - 1 - i
                factor = 1.0 - 0.35 * (forward_i / max(1, n - 1))
                base_color = tuple(int(c * factor) for c in SNAKE_BODY_COLOR)

            color = tuple(min(255, c + 40) for c in base_color) if blink else base_color

            rect = pygame.Rect(px + inset, py + inset, CELL_SIZE - inset * 2, CELL_SIZE - inset * 2)
            pygame.draw.rect(surface, SNAKE_OUTLINE, rect.inflate(4, 4), border_radius=7)
            pygame.draw.rect(surface, color, rect, border_radius=7)

            # Head inner highlight
            if is_head:
                highlight_color = tuple(min(255, c + 60) for c in SNAKE_HEAD_COLOR)
                hi_inset = inset + 4
                hi_rect = pygame.Rect(
                    px + hi_inset, py + hi_inset,
                    CELL_SIZE - hi_inset * 2, CELL_SIZE - hi_inset * 2,
                )
                if hi_rect.width > 2 and hi_rect.height > 2:
                    pygame.draw.rect(surface, highlight_color, hi_rect, border_radius=4)

        hx, hy = grid_to_pixel(self.head)
        cx = hx + CELL_SIZE // 2
        cy = hy + CELL_SIZE // 2
        dx, dy = self.direction
        if (dx, dy) == (1, 0):
            eyes = [(cx + 4, cy - 4), (cx + 4, cy + 4)]
        elif (dx, dy) == (-1, 0):
            eyes = [(cx - 4, cy - 4), (cx - 4, cy + 4)]
        elif (dx, dy) == (0, -1):
            eyes = [(cx - 4, cy - 4), (cx + 4, cy - 4)]
        else:
            eyes = [(cx - 4, cy + 4), (cx + 4, cy + 4)]
        for ex, ey in eyes:
            pygame.draw.circle(surface, (15, 20, 15), (ex, ey), 2)
