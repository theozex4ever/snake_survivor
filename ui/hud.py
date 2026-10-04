import math

import pygame

from constants import (
    TEXT_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT,
    UI_PANEL_BG, UI_PANEL_BORDER, UI_SUBTEXT,
    SNAKE_HEAD_COLOR, HEART_COLOR,
)

_PANEL_ALPHA = 200


def _draw_panel(surface: pygame.Surface, rect: pygame.Rect, radius: int = 14) -> None:
    """Draw a semi-transparent rounded panel."""
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*UI_PANEL_BG, _PANEL_ALPHA), panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, (*UI_PANEL_BORDER, _PANEL_ALPHA), panel.get_rect(), width=1, border_radius=radius)
    surface.blit(panel, rect.topleft)


class HUD:
    def __init__(
        self,
        font: pygame.font.Font,
        big_font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        self.font = font
        self.big_font = big_font
        self.small_font = small_font

    def draw(self, surface: pygame.Surface, snake, score: int, wave: int) -> None:
        hp = snake.hp

        # --- top-left info panel ---
        panel_rect = pygame.Rect(12, 12, 180, 130)
        _draw_panel(surface, panel_rect)

        px, py = panel_rect.x + 14, panel_rect.y + 10

        wave_surf = self.font.render(f"Wave  {wave}", True, SNAKE_HEAD_COLOR)
        surface.blit(wave_surf, (px, py))

        score_surf = self.small_font.render(f"Score  {score}", True, UI_SUBTEXT)
        surface.blit(score_surf, (px, py + 30))

        len_surf = self.small_font.render(f"Length  {len(snake.segments)}", True, UI_SUBTEXT)
        surface.blit(len_surf, (px, py + 50))

        # --- HP hearts ---
        heart_y = py + 80
        for i in range(hp):
            self._draw_heart(surface, px + i * 24, heart_y, size=8)

    def _draw_heart(self, surface: pygame.Surface, x: int, y: int, size: int = 8) -> None:
        r = size
        pygame.draw.circle(surface, HEART_COLOR, (x, y), r)
        pygame.draw.circle(surface, HEART_COLOR, (x + r * 2, y), r)
        pygame.draw.polygon(surface, HEART_COLOR, [
            (x - r, y + 2),
            (x + r * 3, y + 2),
            (x + r, y + r * 2 + 2),
        ])

    def draw_low_hp_vignette(self, surface: pygame.Surface, hp: int, max_hp: int) -> None:
        if hp > 2:
            return
        intensity = max(0.0, (2 - hp + 1) / 3.0)
        ticks = pygame.time.get_ticks()
        pulse = 0.5 + 0.5 * math.sin(ticks / 300)
        alpha = int(80 * intensity * pulse)
        if alpha <= 0:
            return
        thickness = 60
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        color = (220, 80, 110, alpha)
        pygame.draw.rect(vignette, color, (0, 0, SCREEN_WIDTH, thickness))
        pygame.draw.rect(vignette, color, (0, SCREEN_HEIGHT - thickness, SCREEN_WIDTH, thickness))
        pygame.draw.rect(vignette, color, (0, 0, thickness, SCREEN_HEIGHT))
        pygame.draw.rect(vignette, color, (SCREEN_WIDTH - thickness, 0, thickness, SCREEN_HEIGHT))
        surface.blit(vignette, (0, 0))

    def draw_game_over(self, surface: pygame.Surface, score: int) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        panel_w, panel_h = 480, 200
        panel_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - panel_w // 2,
            SCREEN_HEIGHT // 2 - panel_h // 2,
            panel_w, panel_h,
        )
        _draw_panel(surface, panel_rect, radius=20)

        cx = SCREEN_WIDTH // 2
        title = self.big_font.render("Game Over", True, TEXT_COLOR)
        surface.blit(title, title.get_rect(center=(cx, panel_rect.centery - 36)))

        score_surf = self.font.render(f"Score  {score}", True, UI_SUBTEXT)
        surface.blit(score_surf, score_surf.get_rect(center=(cx, panel_rect.centery + 4)))

        hint = self.small_font.render("Press R to return to menu", True, UI_SUBTEXT)
        surface.blit(hint, hint.get_rect(center=(cx, panel_rect.centery + 38)))
