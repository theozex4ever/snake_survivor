import math
import os
import random
from typing import List, Optional, Tuple

import pygame

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, FPS, TITLE,
    BG_COLOR, GRID_COLOR, FOOD_COLOR, FOOD_GLOW,
    ENEMY_COLOR, BULLET_COLOR, BULLET_GLOW, PARTICLE_COLORS,
    SHAKE_DECAY, MAX_SHAKE_OFFSET,
    SHAKE_TRAUMA_PLAYER_HIT, SHAKE_TRAUMA_ENEMY_KILL, SHAKE_TRAUMA_WAVE_START,
    SPEED_OPTIONS, DEFAULT_SPEED_INDEX,
    WAVE_BANNER_DURATION, HIGH_SCORE_FILE,
    STARTING_PLAYER_HP,
)

MAX_FRAME_DT = 0.05  # clamp frame spikes so a stall can't skip a move or enemy hit
SPAWN_TELEGRAPH_TIME = 0.8
from utils import cell_center
from entities import Particle
from run import (
    Run, Shot, FoodEaten, EnemyHit, EnemyContact, EnemySpawned, WaveCleared, RunOver,
)
from systems.sound_manager import SoundManager
from ui.hud import HUD
from ui.screens import draw_speed_select, draw_upgrade_pick, draw_menu, draw_pause, draw_wave_banner

STEER_KEYS = {
    pygame.K_w: (0, -1), pygame.K_UP: (0, -1),
    pygame.K_s: (0, 1), pygame.K_DOWN: (0, 1),
    pygame.K_a: (-1, 0), pygame.K_LEFT: (-1, 0),
    pygame.K_d: (1, 0), pygame.K_RIGHT: (1, 0),
}
PICK_KEYS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
SPEED_KEYS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}


def _opaque_surface() -> pygame.Surface:
    return pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32, (0xFF0000, 0xFF00, 0xFF, 0))


class Game:
    """The app around a Run: window, screens, input, sound, effects and the high score.

    States: "menu", "speed_select", "playing" (a Run exists) and "paused".
    While playing, what's on screen follows the Run's phase.
    """

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        # Everything is drawn on opaque canvases and copied to the window once per
        # frame. Some window surfaces (e.g. KDE Wayland) carry an alpha channel, and
        # translucent blits onto them leave transparent holes that show as black.
        self.screen = _opaque_surface()
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("poppins", 22)
        self.big_font = pygame.font.SysFont("poppins", 36, bold=True)
        self.small_font = pygame.font.SysFont("poppins", 16)
        self.hud = HUD(self.font, self.big_font, self.small_font)

        self.speed_index = DEFAULT_SPEED_INDEX
        self.game_surface = _opaque_surface()
        self._upgrade_card_rects: List[pygame.Rect] = []
        self.running = True

        self.sound_mgr = SoundManager()
        self.sound_mgr.load()
        self._high_score = self._load_high_score()

        self.run: Optional[Run] = None
        self.particles: List[Particle] = []
        self.shake_trauma = 0.0
        self._wave_banner_timer = 0.0
        self._spawn_telegraphs: list = []  # list of [pos: pygame.Vector2, timer: float]
        self.state = "menu"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_high_score(self) -> int:
        path = os.path.join(os.path.dirname(__file__), HIGH_SCORE_FILE)
        try:
            return int(open(path).read().strip())
        except Exception:
            return 0

    def _save_high_score(self, score: int) -> None:
        if score > self._high_score:
            self._high_score = score
            path = os.path.join(os.path.dirname(__file__), HIGH_SCORE_FILE)
            try:
                open(path, 'w').write(str(self._high_score))
            except Exception:
                pass

    def _start_run(self, rng: Optional[random.Random] = None) -> None:
        self.run = Run(SPEED_OPTIONS[self.speed_index][1], rng=rng)
        self.particles = []
        self.shake_trauma = 0.0
        self._wave_banner_timer = 0.0
        self._spawn_telegraphs = []
        self.state = "playing"

    def _choosing_upgrade(self) -> bool:
        """The Run waits on a pick and the wave banner has finished."""
        return self.run.phase == "choosing_upgrade" and self._wave_banner_timer <= 0

    def add_trauma(self, amount: float) -> None:
        self.shake_trauma = min(1.0, self.shake_trauma + amount)

    # ------------------------------------------------------------------
    # Effects
    # ------------------------------------------------------------------

    def _react(self, event) -> None:
        if isinstance(event, Shot):
            self._spawn_muzzle_particles(event.origin, event.direction)
            self.sound_mgr.play("shoot")
        elif isinstance(event, FoodEaten):
            self._spawn_hit_particles(event.pos, FOOD_GLOW, count=10)
            self.sound_mgr.play("eat_food")
        elif isinstance(event, EnemyHit):
            self._spawn_hit_particles(event.pos, ENEMY_COLOR, count=18 if event.killed else 8)
            if event.killed:
                self.add_trauma(SHAKE_TRAUMA_ENEMY_KILL)
                self.sound_mgr.play("kill_enemy")
            else:
                self.sound_mgr.play("hit_enemy")
        elif isinstance(event, EnemyContact):
            self.add_trauma(SHAKE_TRAUMA_PLAYER_HIT)
            self._spawn_hit_particles(event.enemy_pos, (255, 100, 100), count=20)
            self._spawn_hit_particles(event.head_pos, (100, 255, 160), count=12)
            self.sound_mgr.play("player_hurt")
        elif isinstance(event, EnemySpawned):
            self._spawn_telegraphs.append([event.pos, SPAWN_TELEGRAPH_TIME])
        elif isinstance(event, WaveCleared):
            self.add_trauma(SHAKE_TRAUMA_WAVE_START)
            self.sound_mgr.play("wave_complete")
            self._wave_banner_timer = WAVE_BANNER_DURATION
        elif isinstance(event, RunOver):
            self.sound_mgr.play("game_over")
            self._save_high_score(event.score)

    def _spawn_muzzle_particles(self, origin: pygame.Vector2, direction: pygame.Vector2) -> None:
        for _ in range(6):
            spread = pygame.Vector2(
                direction.x + random.uniform(-0.5, 0.5),
                direction.y + random.uniform(-0.5, 0.5),
            )
            if spread.length_squared() > 0:
                spread = spread.normalize()
            self.particles.append(Particle(
                pos=origin.copy(),
                vel=spread * random.uniform(50, 140),
                color=random.choice([BULLET_COLOR, BULLET_GLOW, (255, 255, 255)]),
                life=random.uniform(0.12, 0.25),
                max_life=0.25,
                radius=random.uniform(2, 4),
            ))

    def _spawn_hit_particles(self, pos: pygame.Vector2, base_color: Tuple[int, int, int], count: int = 12) -> None:
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(50, 220)
            self.particles.append(Particle(
                pos=pos.copy(),
                vel=vel,
                color=base_color if random.random() < 0.7 else random.choice(PARTICLE_COLORS),
                life=random.uniform(0.2, 0.45),
                max_life=0.45,
                radius=random.uniform(2, 5),
            ))

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def process_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.run is not None:
                    self._save_high_score(self.run.score)
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m and self.state != "menu":
                    self.sound_mgr.toggle_mute()
                elif self.state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "speed_select"
                elif self.state == "speed_select":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.speed_index = max(0, self.speed_index - 1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.speed_index = min(len(SPEED_OPTIONS) - 1, self.speed_index + 1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._start_run()
                    elif event.key in SPEED_KEYS:
                        self.speed_index = SPEED_KEYS[event.key]
                        self._start_run()
                elif self.state == "paused":
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.state = "playing"
                elif self._choosing_upgrade():
                    if event.key in PICK_KEYS and PICK_KEYS[event.key] < len(self.run.offers):
                        self.run.pick_upgrade(self.run.offers[PICK_KEYS[event.key]].key)
                    elif event.key == pygame.K_p:
                        self.state = "paused"
                elif event.key in STEER_KEYS:
                    self.run.steer(STEER_KEYS[event.key])
                elif event.key == pygame.K_p and self.run.phase == "playing":
                    self.state = "paused"
                elif event.key == pygame.K_r and self.run.phase == "over":
                    self.run = None
                    self.state = "menu"
            elif (event.type == pygame.MOUSEBUTTONDOWN and self.state == "playing"
                  and self._choosing_upgrade()):
                for i, rect in enumerate(self._upgrade_card_rects):
                    if rect.collidepoint(event.pos) and i < len(self.run.offers):
                        self.run.pick_upgrade(self.run.offers[i].key)
                        break

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.state != "playing":
            return

        self.shake_trauma = max(0.0, self.shake_trauma - SHAKE_DECAY * dt)
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]
        self._spawn_telegraphs = [[p, t - dt] for p, t in self._spawn_telegraphs if t - dt > 0]
        if self._wave_banner_timer > 0:
            self._wave_banner_timer -= dt

        for event in self.run.step(dt):
            self._react(event)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self) -> None:
        self._render()
        self.window.blit(self.screen, (0, 0))
        pygame.display.flip()

    def _render(self) -> None:
        if self.state == "menu":
            draw_menu(self.screen, self.big_font, self.font, self.small_font, self._high_score)
            return

        if self.state == "speed_select":
            draw_speed_select(self.screen, self.big_font, self.font, self.small_font, self.speed_index)
            return

        self._draw_world()

        if self.state == "paused":
            self._blit_with_shake()
            draw_pause(self.screen, self.big_font, self.font)
            return

        if self.run.phase == "choosing_upgrade":
            if self._wave_banner_timer > 0:
                self._blit_with_shake()
                draw_wave_banner(self.screen, self.big_font, self.font, self.run.wave)
            else:
                self._upgrade_card_rects = draw_upgrade_pick(
                    self.screen, self.game_surface,
                    self.big_font, self.font, self.small_font,
                    self.run.offers,
                )
            return

        self._blit_with_shake()

    def _draw_world(self) -> None:
        run = self.run

        # --- grid ---
        self.game_surface.fill(BG_COLOR)
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            pygame.draw.line(self.game_surface, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.game_surface, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

        # --- food ---
        c = cell_center(run.food)
        glow = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*FOOD_GLOW, 70), (15, 15), 12)
        self.game_surface.blit(glow, (c.x - 15, c.y - 15))
        pygame.draw.circle(self.game_surface, FOOD_COLOR, (int(c.x), int(c.y)), 7)

        # --- spawn telegraphs ---
        for pos, t in self._spawn_telegraphs:
            alpha = int(255 * t / SPAWN_TELEGRAPH_TIME)
            dx = SCREEN_WIDTH / 2 - pos.x
            dy = SCREEN_HEIGHT / 2 - pos.y
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                nx, ny = dx / length, dy / length  # unit vector toward center
                px, py = -ny, nx                   # perpendicular
                tip = (int(pos.x + nx * 18), int(pos.y + ny * 18))
                bl  = (int(pos.x + px * 8),  int(pos.y + py * 8))
                br  = (int(pos.x - px * 8),  int(pos.y - py * 8))
                surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.polygon(surf, (255, 220, 60, alpha), [tip, bl, br])
                self.game_surface.blit(surf, (0, 0))

        for p in self.particles:
            p.draw(self.game_surface)
        for b in run.bullets:
            b.draw(self.game_surface)
        for e in run.enemies:
            e.draw(self.game_surface)
        run.snake.draw(self.game_surface)

        self.hud.draw(self.game_surface, run.snake, run.score, run.wave)
        self.hud.draw_low_hp_vignette(self.game_surface, run.snake.hp, STARTING_PLAYER_HP)
        if run.phase == "over":
            self.hud.draw_game_over(self.game_surface, run.score)

    def _blit_with_shake(self) -> None:
        shake_amount = self.shake_trauma ** 2
        if shake_amount > 0.001:
            ox = int(random.uniform(-1, 1) * MAX_SHAKE_OFFSET * shake_amount)
            oy = int(random.uniform(-1, 1) * MAX_SHAKE_OFFSET * shake_amount)
            self.screen.fill(BG_COLOR)
            self.screen.blit(self.game_surface, (ox, oy))
        else:
            self.screen.blit(self.game_surface, (0, 0))

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run_loop(self) -> None:
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, MAX_FRAME_DT)
            self.process_input()
            self.update(dt)
            self.draw()
        pygame.quit()
