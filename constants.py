from typing import List, Tuple

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 720
CELL_SIZE = 22

GRID_WIDTH = SCREEN_WIDTH // CELL_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // CELL_SIZE

FPS = 60
TITLE = "Snake Shooter"

BG_COLOR = (20, 18, 30)
GRID_COLOR = (28, 26, 42)
TEXT_COLOR = (228, 222, 238)

SNAKE_HEAD_COLOR = (148, 232, 183)
SNAKE_BODY_COLOR = (100, 185, 143)
SNAKE_OUTLINE = (52, 110, 80)

FOOD_COLOR = (255, 198, 112)
FOOD_GLOW = (255, 228, 168)

BULLET_COLOR = (142, 198, 244)
BULLET_GLOW = (188, 222, 255)

ENEMY_COLOR = (224, 123, 138)
ENEMY_OUTLINE = (155, 72, 88)
HP_BAR_BG = (44, 26, 34)
HP_BAR_FILL = (132, 218, 153)

PARTICLE_COLORS = [
    (255, 168, 148),
    (255, 222, 148),
    (158, 212, 255),
    (158, 242, 192),
]

# UI design system
UI_ACCENT = (182, 162, 218)       # lavender — selected states & highlights
UI_SUBTEXT = (138, 132, 158)      # muted secondary text
UI_PANEL_BG = (28, 26, 42)        # dark translucent panel background
UI_PANEL_BORDER = (72, 65, 108)   # subtle purple panel border
HEART_COLOR = (232, 120, 148)     # soft rose hearts

# timing / balance
SNAKE_MOVE_INTERVAL = 0.10
AUTO_SHOOT_INTERVAL = 0.60
ENEMY_SPAWN_GAP = 0.55
INVULN_TIME = 0.75

INITIAL_SNAKE_LENGTH = 5
STARTING_PLAYER_HP = 5

BASE_ENEMY_SPEED = 68.0
BASE_ENEMY_HP = 2
BULLET_SPEED = 520.0
BULLET_RADIUS = 4

PLAYER_COLLISION_RADIUS = CELL_SIZE * 0.42
ENEMY_TOUCH_DAMAGE = 1

FOOD_SCORE = 10
ENEMY_KILL_SCORE = 20

SHAKE_DECAY = 1.8
MAX_SHAKE_OFFSET = 14
SHAKE_TRAUMA_PLAYER_HIT = 0.75
SHAKE_TRAUMA_ENEMY_KILL = 0.25
SHAKE_TRAUMA_WAVE_START = 0.12

SPEED_OPTIONS: List[Tuple[str, float]] = [
    ("Relaxed", 0.18),   #  ~5.5 moves/s
    ("Normal",  0.10),   # ~10.0 moves/s  ← default
    ("Fast",    0.07),   # ~14.3 moves/s
    ("Blazing", 0.05),   # ~20.0 moves/s
]
DEFAULT_SPEED_INDEX = 1

LOW_HP_THRESHOLD = 2
WAVE_BANNER_DURATION = 1.5   # seconds the "Wave N Complete!" banner shows
HIGH_SCORE_FILE = "highscore.txt"  # path relative to snake_survivor/
