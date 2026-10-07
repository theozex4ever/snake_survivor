from typing import List

import pygame

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR,
    SNAKE_HEAD_COLOR, SNAKE_BODY_COLOR, TEXT_COLOR, GRID_COLOR,
    SPEED_OPTIONS,
    UI_ACCENT, UI_PANEL_BG, UI_PANEL_BORDER, UI_SUBTEXT, HEART_COLOR,
)
from upgrades import Offer

_PANEL_ALPHA = 210


def _draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    radius: int = 18,
    border_color=None,
    border_width: int = 1,
    alpha: int = _PANEL_ALPHA,
) -> None:
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*UI_PANEL_BG, alpha), panel.get_rect(), border_radius=radius)
    bc = border_color if border_color is not None else UI_PANEL_BORDER
    pygame.draw.rect(panel, (*bc, alpha), panel.get_rect(), width=border_width, border_radius=radius)
    surface.blit(panel, rect.topleft)


def _dim_overlay(surface: pygame.Surface, alpha: int = 150) -> None:
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surface.blit(overlay, (0, 0))


# ---------------------------------------------------------------------------
# Menu screen
# ---------------------------------------------------------------------------

def draw_menu(
    screen: pygame.Surface,
    big_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    high_score: int,
) -> None:
    screen.fill(BG_COLOR)

    # Subtle grid
    for x in range(0, SCREEN_WIDTH, 44):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 44):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

    cx = SCREEN_WIDTH // 2

    # Central card
    card_w, card_h = 520, 300
    card = pygame.Rect(cx - card_w // 2, SCREEN_HEIGHT // 2 - card_h // 2, card_w, card_h)
    _draw_panel(screen, card, radius=24, border_color=UI_ACCENT, border_width=2)

    title = big_font.render("Snake Shooter", True, SNAKE_HEAD_COLOR)
    screen.blit(title, title.get_rect(center=(cx, card.top + 60)))

    sub = small_font.render("A semi-idle survivor roguelite", True, UI_SUBTEXT)
    screen.blit(sub, sub.get_rect(center=(cx, card.top + 98)))

    # Decorative snake strip
    seg = 14
    gap = 4
    n = 8
    strip_w = n * (seg + gap) - gap
    sx = cx - strip_w // 2
    sy = card.top + 140
    for k in range(n):
        factor = 1.0 - 0.4 * (k / max(1, n - 1))
        col = (
            int(SNAKE_HEAD_COLOR[0] * factor),
            int(SNAKE_HEAD_COLOR[1] * factor),
            int(SNAKE_HEAD_COLOR[2] * factor),
        ) if k > 0 else SNAKE_HEAD_COLOR
        rx = sx + k * (seg + gap)
        pygame.draw.rect(screen, col, (rx, sy, seg, seg), border_radius=5)

    enter_surf = font.render("Press  Enter  to  start", True, TEXT_COLOR)
    screen.blit(enter_surf, enter_surf.get_rect(center=(cx, card.top + 194)))

    if high_score > 0:
        hs = small_font.render(f"Best  {high_score}", True, UI_ACCENT)
        screen.blit(hs, hs.get_rect(center=(cx, card.top + 230)))



# ---------------------------------------------------------------------------
# Pause overlay
# ---------------------------------------------------------------------------

def draw_pause(
    screen: pygame.Surface,
    big_font: pygame.font.Font,
    font: pygame.font.Font,
) -> None:
    _dim_overlay(screen, alpha=140)

    card_w, card_h = 380, 150
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    card = pygame.Rect(cx - card_w // 2, cy - card_h // 2, card_w, card_h)
    _draw_panel(screen, card, radius=20, border_color=UI_ACCENT, border_width=2)

    paused = big_font.render("Paused", True, TEXT_COLOR)
    screen.blit(paused, paused.get_rect(center=(cx, cy - 22)))

    resume = font.render("Press  P  to  resume", True, UI_SUBTEXT)
    screen.blit(resume, resume.get_rect(center=(cx, cy + 26)))



# ---------------------------------------------------------------------------
# Wave-clear banner
# ---------------------------------------------------------------------------

def draw_wave_banner(
    screen: pygame.Surface,
    big_font: pygame.font.Font,
    font: pygame.font.Font,
    wave_num: int,
) -> None:
    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

    card_w, card_h = 540, 140
    card = pygame.Rect(cx - card_w // 2, cy - card_h // 2, card_w, card_h)
    _draw_panel(screen, card, radius=20, border_color=SNAKE_HEAD_COLOR, border_width=2)

    wave_surf = big_font.render(f"Wave  {wave_num}  Complete!", True, SNAKE_HEAD_COLOR)
    screen.blit(wave_surf, wave_surf.get_rect(center=(cx, cy - 18)))

    sub = font.render("Choosing upgrade…", True, UI_SUBTEXT)
    screen.blit(sub, sub.get_rect(center=(cx, cy + 26)))



# ---------------------------------------------------------------------------
# Speed select
# ---------------------------------------------------------------------------

def draw_speed_select(
    screen: pygame.Surface,
    big_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    speed_index: int,
) -> None:
    screen.fill(BG_COLOR)

    for x in range(0, SCREEN_WIDTH, 44):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, 44):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

    cx = SCREEN_WIDTH // 2
    cy = SCREEN_HEIGHT // 2

    title = big_font.render("Choose  Speed", True, TEXT_COLOR)
    screen.blit(title, title.get_rect(center=(cx, cy - 148)))

    prompt = small_font.render("Left / Right  navigate     Enter  confirm     1–4  pick directly", True, UI_SUBTEXT)
    screen.blit(prompt, prompt.get_rect(center=(cx, cy - 110)))

    card_w, card_h = 200, 120
    gap = 20
    total_w = len(SPEED_OPTIONS) * card_w + (len(SPEED_OPTIONS) - 1) * gap
    start_x = cx - total_w // 2

    for i, (label, interval) in enumerate(SPEED_OPTIONS):
        x = start_x + i * (card_w + gap)
        rect = pygame.Rect(x, cy - card_h // 2, card_w, card_h)
        selected = i == speed_index

        bc = UI_ACCENT if selected else UI_PANEL_BORDER
        bw = 2 if selected else 1
        _draw_panel(screen, rect, radius=16, border_color=bc, border_width=bw, alpha=220)

        name_col = UI_ACCENT if selected else TEXT_COLOR
        name_surf = font.render(label, True, name_col)
        screen.blit(name_surf, name_surf.get_rect(center=(rect.centerx, rect.centery - 24)))

        mps_surf = small_font.render(f"{1 / interval:.1f}  moves/s", True, UI_SUBTEXT)
        screen.blit(mps_surf, mps_surf.get_rect(center=(rect.centerx, rect.centery + 8)))

        hint_col = UI_ACCENT if selected else UI_SUBTEXT
        hint_surf = small_font.render(f"[ {i + 1} ]", True, hint_col)
        screen.blit(hint_surf, hint_surf.get_rect(center=(rect.centerx, rect.centery + 36)))



# ---------------------------------------------------------------------------
# Upgrade pick
# ---------------------------------------------------------------------------

def draw_upgrade_pick(
    screen: pygame.Surface,
    game_surface: pygame.Surface,
    big_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    offers: List[Offer],
) -> List[pygame.Rect]:
    screen.blit(game_surface, (0, 0))
    _dim_overlay(screen, alpha=170)

    cx = SCREEN_WIDTH // 2

    title = big_font.render("Choose  an  Upgrade", True, TEXT_COLOR)
    screen.blit(title, title.get_rect(center=(cx, 100)))

    card_w, card_h = 290, 240
    gap = 24
    n = len(offers)
    total_w = n * card_w + (n - 1) * gap
    start_x = cx - total_w // 2
    cy = SCREEN_HEIGHT // 2 + 20

    card_rects: List[pygame.Rect] = []
    for i, offer in enumerate(offers):
        x = start_x + i * (card_w + gap)
        rect = pygame.Rect(x, cy - card_h // 2, card_w, card_h)
        card_rects.append(rect)

        _draw_panel(screen, rect, radius=20, border_color=UI_ACCENT, border_width=2)

        num_surf = big_font.render(str(i + 1), True, UI_ACCENT)
        screen.blit(num_surf, num_surf.get_rect(center=(rect.centerx, rect.top + 32)))

        name_surf = font.render(offer.name, True, TEXT_COLOR)
        screen.blit(name_surf, name_surf.get_rect(center=(rect.centerx, rect.centery - 20)))

        desc_surf = small_font.render(offer.desc, True, UI_SUBTEXT)
        screen.blit(desc_surf, desc_surf.get_rect(center=(rect.centerx, rect.centery + 12)))

        # Preview lines stack upward from the bottom of the card.
        for j, line in enumerate(reversed(offer.preview)):
            stat_surf = small_font.render(line, True, SNAKE_HEAD_COLOR)
            screen.blit(stat_surf, stat_surf.get_rect(center=(rect.centerx, rect.bottom - 32 - j * 22)))

    hint = small_font.render("1  /  2  /  3   or   click", True, UI_SUBTEXT)
    screen.blit(hint, hint.get_rect(center=(cx, cy + card_h // 2 + 28)))

    return card_rects
