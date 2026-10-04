import random
from typing import List

UPGRADE_POOL: List[dict] = [
    {
        "key": "faster_fire",
        "name": "Faster Fire",
        "desc": "Fire rate ×1.25",
        "stat": lambda g: f"{1/g.shoot_interval:.2f}  →  {1/(g.shoot_interval*0.80):.2f} shots/s",
    },
    {
        "key": "extra_heart",
        "name": "Extra Heart",
        "desc": "+1 max HP",
        "stat": lambda g: f"HP:  {g.snake.hp}  →  {g.snake.hp + 1}",
    },
    {
        "key": "big_bullet",
        "name": "Big Bullet",
        "desc": "+2 radius, +1 damage",
        "stat": lambda g: f"Dmg:  {g.bullet_damage}  →  {g.bullet_damage + 1}",
    },
    {
        "key": "thick_skin",
        "name": "Thick Skin",
        "desc": "+0.30 s invulnerability on hit",
        "stat": lambda g: f"Invuln:  {g.invuln_time:.2f}  →  {g.invuln_time + 0.30:.2f} s",
    },
    {
        "key": "swift_snake",
        "name": "Swift Snake",
        "desc": "Move speed ×1.11",
        "stat": lambda g: f"{1/g.move_interval:.1f}  →  {1/(g.move_interval*0.90):.1f} moves/s",
    },
    {
        "key": "piercing_shot",
        "name": "Piercing Shot",
        "desc": "Bullets pass through +1 enemy",
        "stat": lambda g: f"Pierce:  {g.bullet_piercing}  →  {g.bullet_piercing + 1}",
    },
]


def roll(n: int = 3) -> List[dict]:
    return random.sample(UPGRADE_POOL, min(n, len(UPGRADE_POOL)))
