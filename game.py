import math
import os
import random
from typing import List, Optional, Tuple

import pygame

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, FPS, TITLE,
    BG_COLOR, GRID_COLOR, FOOD_COLOR, FOOD_GLOW,
    ENEMY_COLOR, BULLET_COLOR, BULLET_GLOW, PARTICLE_COLORS,
    AUTO_SHOOT_INTERVAL, BULLET_SPEED, BULLET_RADIUS, INVULN_TIME,
    FOOD_SCORE, ENEMY_KILL_SCORE, PLAYER_COLLISION_RADIUS, ENEMY_TOUCH_DAMAGE,
    SHAKE_DECAY, MAX_SHAKE_OFFSET,
    SHAKE_TRAUMA_PLAYER_HIT, SHAKE_TRAUMA_ENEMY_KILL, SHAKE_TRAUMA_WAVE_START,
    SPEED_OPTIONS, DEFAULT_SPEED_INDEX,
    LOW_HP_THRESHOLD, WAVE_BANNER_DURATION, HIGH_SCORE_FILE,
    STARTING_PLAYER_HP,
)

MAX_FRAME_DT = 0.05  # clamp frame spikes so a stall can't skip a move or enemy hit
from utils import cell_center, random_empty_cell
from entities import Snake, Enemy, Bullet, Particle
from systems.wave_manager import WaveManager
from systems.upgrade_system import roll as roll_upgrades
from systems.sound_manager import SoundManager
from ui.hud import HUD
from ui.screens import draw_speed_select, draw_upgrade_pick, draw_menu, draw_pause, draw_wave_banner


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("poppins", 22)
        self.big_font = pygame.font.SysFont("poppins", 36, bold=True)
        self.small_font = pygame.font.SysFont("poppins", 16)
        self.hud = HUD(self.font, self.big_font, self.small_font)

        self.speed_index = DEFAULT_SPEED_INDEX
        self.move_interval = SPEED_OPTIONS[self.speed_index][1]
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._upgrade_card_rects: List[pygame.Rect] = []
        self.wave_mgr = WaveManager()
        self.running = True

        self.sound_mgr = SoundManager()
        self.sound_mgr.load()
        self._resume_state = "playing"
        self._wave_banner_timer = 0.0
        self._high_score = self._load_high_score()

        self.reset()
        self.state = "menu"

    def reset(self) -> None:
        self.state = "speed_select"
        self.snake = Snake()
        self.score = 0

        self.bullets: List[Bullet] = []
        self.enemies: List[Enemy] = []
        self.particles: List[Particle] = []

        self.shake_trauma = 0.0
        self.shoot_interval = AUTO_SHOOT_INTERVAL
        self.bullet_speed = BULLET_SPEED
        self.bullet_radius = BULLET_RADIUS
        self.bullet_damage = 1
        self.bullet_piercing = 0
        self.invuln_time = INVULN_TIME
        self.offered_upgrades: List[dict] = []

        self.move_timer = 0.0
        self.shoot_timer = 0.0
        self.wave_mgr.reset()
        self._wave_banner_timer = 0.0
        self._spawn_telegraphs: list = []  # list of [pos: pygame.Vector2, timer: float]

        self.food = self.spawn_food()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_high_score(self) -> int:
        path = os.path.join(os.path.dirname(__file__), HIGH_SCORE_FILE)
        try:
            return int(open(path).read().strip())
        except Exception:
            return 0

    def _save_high_score(self) -> None:
        if self.score > self._high_score:
            self._high_score = self.score
            path = os.path.join(os.path.dirname(__file__), HIGH_SCORE_FILE)
            try:
                open(path, 'w').write(str(self._high_score))
            except Exception:
                pass

    def _on_game_over(self) -> None:
        self.sound_mgr.play("game_over")
        self._save_high_score()

    def _confirm_speed(self) -> None:
        self.move_interval = SPEED_OPTIONS[self.speed_index][1]
        self.state = "playing"
        self.move_timer = 0.0
        self.shoot_timer = 0.0

    def add_trauma(self, amount: float) -> None:
        self.shake_trauma = min(1.0, self.shake_trauma + amount)

    def _roll_upgrades(self) -> None:
        self.offered_upgrades = roll_upgrades()

    def _apply_upgrade(self, key: str) -> None:
        if key == "faster_fire":
            self.shoot_interval = max(0.08, self.shoot_interval * 0.80)
        elif key == "extra_heart":
            self.snake.hp += 1
        elif key == "big_bullet":
            self.bullet_radius += 2
            self.bullet_damage += 1
        elif key == "thick_skin":
            self.invuln_time += 0.30
        elif key == "swift_snake":
            self.move_interval = max(0.04, self.move_interval * 0.90)
        elif key == "piercing_shot":
            self.bullet_piercing += 1

        self.offered_upgrades = []
        self.wave_mgr.advance()
        self.state = "playing"

    # ------------------------------------------------------------------
    # Spawning
    # ------------------------------------------------------------------

    def spawn_food(self) -> Tuple[int, int]:
        return random_empty_cell(self.snake.occupied_cells())

    def spawn_enemy(self) -> None:
        hp = self.wave_mgr.enemy_hp()
        pos = self.wave_mgr.random_spawn_pos()
        pos_copy = pygame.Vector2(pos)
        self.enemies.append(Enemy(
            pos=pos,
            speed=self.wave_mgr.enemy_speed(),
            max_hp=hp,
            hp=hp,
        ))
        self._spawn_telegraphs.append([pos_copy, 0.8])

    def nearest_enemy(self) -> Optional[Enemy]:
        living = [e for e in self.enemies if e.alive]
        if not living:
            return None
        head = self.snake.head_center()
        return min(living, key=lambda e: (e.pos - head).length_squared())

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def auto_shoot(self) -> None:
        target = self.nearest_enemy()
        if target is None:
            return
        origin = self.snake.head_center()
        delta = target.pos - origin
        if delta.length_squared() < 0.001:
            return
        direction = delta.normalize()
        self.bullets.append(Bullet(
            pos=origin.copy(),
            vel=direction * self.bullet_speed,
            radius=self.bullet_radius,
            damage=self.bullet_damage,
            piercing=self.bullet_piercing,
        ))
        self._spawn_muzzle_particles(origin, direction)
        self.sound_mgr.play("shoot")

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
                self._save_high_score()
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "speed_select"
                elif self.state == "speed_select":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.speed_index = max(0, self.speed_index - 1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.speed_index = min(len(SPEED_OPTIONS) - 1, self.speed_index + 1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._confirm_speed()
                    elif event.key == pygame.K_1:
                        self.speed_index = 0; self._confirm_speed()
                    elif event.key == pygame.K_2:
                        self.speed_index = 1; self._confirm_speed()
                    elif event.key == pygame.K_3:
                        self.speed_index = 2; self._confirm_speed()
                    elif event.key == pygame.K_4:
                        self.speed_index = 3; self._confirm_speed()
                    elif event.key == pygame.K_m:
                        self.sound_mgr.toggle_mute()
                elif self.state == "paused":
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.state = self._resume_state
                    elif event.key == pygame.K_m:
                        self.sound_mgr.toggle_mute()
                elif self.state == "upgrade_pick":
                    if event.key == pygame.K_1 and len(self.offered_upgrades) >= 1:
                        self._apply_upgrade(self.offered_upgrades[0]["key"])
                    elif event.key == pygame.K_2 and len(self.offered_upgrades) >= 2:
                        self._apply_upgrade(self.offered_upgrades[1]["key"])
                    elif event.key == pygame.K_3 and len(self.offered_upgrades) >= 3:
                        self._apply_upgrade(self.offered_upgrades[2]["key"])
                    elif event.key == pygame.K_p:
                        self._resume_state = "upgrade_pick"
                        self.state = "paused"
                    elif event.key == pygame.K_m:
                        self.sound_mgr.toggle_mute()
                else:
                    # playing / wave_clear states
                    if event.key in (pygame.K_w, pygame.K_UP):
                        self.snake.set_direction((0, -1))
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        self.snake.set_direction((0, 1))
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        self.snake.set_direction((-1, 0))
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        self.snake.set_direction((1, 0))
                    elif event.key == pygame.K_p and self.state == "playing" and self.snake.alive:
                        self._resume_state = "playing"
                        self.state = "paused"
                    elif event.key == pygame.K_r and not self.snake.alive:
                        self._save_high_score()
                        self.reset()
                        self.state = "menu"
                    elif event.key == pygame.K_m:
                        self.sound_mgr.toggle_mute()
            elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "upgrade_pick":
                for i, rect in enumerate(self._upgrade_card_rects):
                    if rect.collidepoint(event.pos):
                        self._apply_upgrade(self.offered_upgrades[i]["key"])
                        break

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.state in ("menu", "paused", "speed_select"):
            return

        if self.state == "wave_clear":
            self._wave_banner_timer -= dt
            if self._wave_banner_timer <= 0:
                self._roll_upgrades()
                self.state = "upgrade_pick"
            return  # freeze gameplay during banner

        self.shake_trauma = max(0.0, self.shake_trauma - SHAKE_DECAY * dt)
        self.snake.update(dt)

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

        if not self.snake.alive or self.state in ("upgrade_pick", "wave_clear"):
            return

        self.move_timer += dt
        self.shoot_timer += dt

        if self.move_timer >= self.move_interval:
            self.move_timer -= self.move_interval
            self.snake.move()
            # Check if snake died after move
            if not self.snake.alive:
                self._on_game_over()
                return  # freeze the frame so the saved score matches the displayed one
            elif self.snake.head == self.food:
                self.snake.grow(1)
                self.score += FOOD_SCORE
                self._spawn_hit_particles(self.snake.head_center(), FOOD_GLOW, count=10)
                self.food = self.spawn_food()
                self.sound_mgr.play("eat_food")

        self._spawn_telegraphs = [[p, t - dt] for p, t in self._spawn_telegraphs if t - dt > 0]

        living_count = sum(1 for e in self.enemies if e.alive)
        signal = self.wave_mgr.update(dt, living_count)
        if signal == "spawn":
            self.spawn_enemy()
        elif signal == "wave_complete":
            self.add_trauma(SHAKE_TRAUMA_WAVE_START)
            self.sound_mgr.play("wave_complete")
            self._wave_banner_timer = WAVE_BANNER_DURATION
            self.state = "wave_clear"

        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer -= self.shoot_interval
            self.auto_shoot()

        head_pos = self.snake.head_center()

        for enemy in self.enemies:
            enemy.update(dt, head_pos)
        for bullet in self.bullets:
            bullet.update(dt)

        for bullet in self.bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive or enemy.uid in bullet.hit_ids:
                    continue
                combined = bullet.radius + enemy.radius
                if (bullet.pos - enemy.pos).length_squared() <= combined * combined:
                    bullet.hit_ids.add(enemy.uid)
                    died = enemy.take_damage(bullet.damage)
                    self._spawn_hit_particles(enemy.pos, ENEMY_COLOR, count=8 if not died else 18)
                    if died:
                        self.score += ENEMY_KILL_SCORE
                        self.add_trauma(SHAKE_TRAUMA_ENEMY_KILL)
                        self.sound_mgr.play("kill_enemy")
                    else:
                        self.sound_mgr.play("hit_enemy")
                    if bullet.piercing > 0:
                        bullet.piercing -= 1
                    else:
                        bullet.alive = False
                    break

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            combined = enemy.radius + PLAYER_COLLISION_RADIUS
            if (enemy.pos - head_pos).length_squared() <= combined * combined:
                enemy.alive = False
                self.snake.take_damage(ENEMY_TOUCH_DAMAGE, self.invuln_time)
                self.add_trauma(SHAKE_TRAUMA_PLAYER_HIT)
                self._spawn_hit_particles(enemy.pos, (255, 100, 100), count=20)
                self._spawn_hit_particles(head_pos, (100, 255, 160), count=12)
                self.sound_mgr.play("player_hurt")
                if not self.snake.alive:
                    self._on_game_over()
                    break

        self.bullets = [b for b in self.bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self) -> None:
        if self.state == "menu":
            draw_menu(self.screen, self.big_font, self.font, self.small_font, self._high_score)
            return

        if self.state == "speed_select":
            draw_speed_select(self.screen, self.big_font, self.font, self.small_font, self.speed_index)
            return

        # --- grid ---
        self.game_surface.fill(BG_COLOR)
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            pygame.draw.line(self.game_surface, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.game_surface, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

        # --- food ---
        c = cell_center(self.food)
        glow = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*FOOD_GLOW, 70), (15, 15), 12)
        self.game_surface.blit(glow, (c.x - 15, c.y - 15))
        pygame.draw.circle(self.game_surface, FOOD_COLOR, (int(c.x), int(c.y)), 7)

        # --- spawn telegraphs ---
        for pos, t in self._spawn_telegraphs:
            alpha = int(255 * t / 0.8)
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
        for b in self.bullets:
            b.draw(self.game_surface)
        for e in self.enemies:
            e.draw(self.game_surface)
        self.snake.draw(self.game_surface)

        self.hud.draw(self.game_surface, self.snake, self.score, self.wave_mgr.wave)
        self.hud.draw_low_hp_vignette(self.game_surface, self.snake.hp, STARTING_PLAYER_HP)
        if not self.snake.alive:
            self.hud.draw_game_over(self.game_surface, self.score)

        if self.state == "wave_clear":
            shake_amount = self.shake_trauma ** 2
            if shake_amount > 0.001:
                ox = int(random.uniform(-1, 1) * MAX_SHAKE_OFFSET * shake_amount)
                oy = int(random.uniform(-1, 1) * MAX_SHAKE_OFFSET * shake_amount)
                self.screen.fill(BG_COLOR)
                self.screen.blit(self.game_surface, (ox, oy))
            else:
                self.screen.blit(self.game_surface, (0, 0))
            draw_wave_banner(self.screen, self.big_font, self.font, self.wave_mgr.wave)
            return

        if self.state == "upgrade_pick":
            self._upgrade_card_rects = draw_upgrade_pick(
                self.screen, self.game_surface,
                self.big_font, self.font, self.small_font,
                self.offered_upgrades, self,
            )
            return

        shake_amount = self.shake_trauma ** 2
        if shake_amount > 0.001:
            ox = int(random.uniform(-1, 1) * MAX_SHAKE_OFFSET * shake_amount)
            oy = int(random.uniform(-1, 1) * MAX_SHAKE_OFFSET * shake_amount)
            self.screen.fill(BG_COLOR)
            self.screen.blit(self.game_surface, (ox, oy))
        else:
            self.screen.blit(self.game_surface, (0, 0))

        if self.state == "paused":
            draw_pause(self.screen, self.big_font, self.font)
            return

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, MAX_FRAME_DT)
            self.process_input()
            self.update(dt)
            self.draw()
        pygame.quit()
