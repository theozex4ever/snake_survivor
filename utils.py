import random
from typing import Tuple

import pygame

from constants import CELL_SIZE, GRID_WIDTH, GRID_HEIGHT


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def grid_to_pixel(cell: Tuple[int, int]) -> Tuple[int, int]:
    return cell[0] * CELL_SIZE, cell[1] * CELL_SIZE


def cell_center(cell: Tuple[int, int]) -> pygame.Vector2:
    x, y = grid_to_pixel(cell)
    return pygame.Vector2(x + CELL_SIZE / 2, y + CELL_SIZE / 2)


def random_empty_cell(occupied: set, rng: random.Random = random) -> Tuple[int, int]:
    free = [
        (x, y)
        for x in range(GRID_WIDTH)
        for y in range(GRID_HEIGHT)
        if (x, y) not in occupied
    ]
    if not free:
        raise ValueError("no empty cell available")
    return rng.choice(free)
