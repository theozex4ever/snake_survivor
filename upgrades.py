"""Upgrades and the Stats they change.

Each Upgrade is defined once, as a function from a run's Stats and the
snake's HP to new ones. An Offer's preview comes from applying that function,
so the card always shows what picking it does.
"""
import random
from dataclasses import dataclass, fields, replace
from typing import Callable, List, Tuple

from constants import AUTO_SHOOT_INTERVAL, BULLET_RADIUS, BULLET_SPEED, INVULN_TIME


@dataclass(frozen=True)
class Stats:
    move_interval: float
    shoot_interval: float = AUTO_SHOOT_INTERVAL
    bullet_speed: float = BULLET_SPEED
    bullet_radius: int = BULLET_RADIUS
    bullet_damage: int = 1
    bullet_piercing: int = 0
    invuln_time: float = INVULN_TIME


@dataclass(frozen=True)
class Upgrade:
    key: str
    name: str
    desc: str
    effect: Callable[[Stats, int], Tuple[Stats, int]]


@dataclass(frozen=True)
class Offer:
    key: str
    name: str
    desc: str
    preview: Tuple[str, ...]


UPGRADES: Tuple[Upgrade, ...] = (
    Upgrade("faster_fire", "Faster Fire", "Fire rate ×1.25",
            lambda s, hp: (replace(s, shoot_interval=max(0.08, s.shoot_interval * 0.80)), hp)),
    Upgrade("extra_heart", "Extra Heart", "+1 HP",
            lambda s, hp: (s, hp + 1)),
    Upgrade("big_bullet", "Big Bullet", "+2 radius, +1 damage",
            lambda s, hp: (replace(s, bullet_radius=s.bullet_radius + 2,
                                   bullet_damage=s.bullet_damage + 1), hp)),
    Upgrade("thick_skin", "Thick Skin", "+0.30 s invulnerability on hit",
            lambda s, hp: (replace(s, invuln_time=s.invuln_time + 0.30), hp)),
    Upgrade("swift_snake", "Swift Snake", "Move speed ×1.11",
            lambda s, hp: (replace(s, move_interval=max(0.04, s.move_interval * 0.90)), hp)),
    Upgrade("piercing_shot", "Piercing Shot", "Bullets pass through +1 enemy",
            lambda s, hp: (replace(s, bullet_piercing=s.bullet_piercing + 1), hp)),
)

# How each value reads on an upgrade card: label, display value, unit.
_DISPLAY = {
    "move_interval": ("Speed", lambda v: f"{1 / v:.1f}", "moves/s"),
    "shoot_interval": ("Fire rate", lambda v: f"{1 / v:.2f}", "shots/s"),
    "bullet_speed": ("Bullet speed", lambda v: f"{v:.0f}", "px/s"),
    "bullet_radius": ("Size", str, "px"),
    "bullet_damage": ("Dmg", str, ""),
    "bullet_piercing": ("Pierce", str, ""),
    "invuln_time": ("Invuln", lambda v: f"{v:.2f}", "s"),
    "hp": ("HP", str, ""),
}


def apply(key: str, stats: Stats, hp: int) -> Tuple[Stats, int]:
    """The Stats and HP after picking the upgrade."""
    return _find(key).effect(stats, hp)


def offer(key: str, stats: Stats, hp: int) -> Offer:
    """The upgrade as a card, previewing what picking it would change."""
    upgrade = _find(key)
    new_stats, new_hp = upgrade.effect(stats, hp)
    before = {f.name: getattr(stats, f.name) for f in fields(Stats)} | {"hp": hp}
    after = {f.name: getattr(new_stats, f.name) for f in fields(Stats)} | {"hp": new_hp}
    preview = tuple(_preview_line(name, before[name], after[name])
                    for name in before if before[name] != after[name])
    return Offer(upgrade.key, upgrade.name, upgrade.desc, preview or ("Already at its limit",))


def offers(stats: Stats, hp: int, rng: random.Random = random, n: int = 3) -> List[Offer]:
    """n distinct upgrades, picked at random."""
    return [offer(u.key, stats, hp) for u in rng.sample(UPGRADES, min(n, len(UPGRADES)))]


def _find(key: str) -> Upgrade:
    for upgrade in UPGRADES:
        if upgrade.key == key:
            return upgrade
    raise ValueError(f"no upgrade called {key!r}")


def _preview_line(name: str, before, after) -> str:
    label, show, unit = _DISPLAY[name]
    return f"{label}:  {show(before)}  ->  {show(after)}" + (f" {unit}" if unit else "")
