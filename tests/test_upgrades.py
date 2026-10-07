import random

import pytest

from constants import AUTO_SHOOT_INTERVAL, BULLET_RADIUS, INVULN_TIME, SPEED_OPTIONS
from upgrades import UPGRADES, Stats, apply, offer, offers

NORMAL = SPEED_OPTIONS[1][1]
HP = 3


@pytest.fixture
def stats():
    return Stats(move_interval=NORMAL)


def test_stats_start_from_the_chosen_speed_and_defaults(stats):
    assert stats.move_interval == NORMAL
    assert stats.shoot_interval == AUTO_SHOOT_INTERVAL
    assert stats.bullet_radius == BULLET_RADIUS
    assert stats.invuln_time == INVULN_TIME
    assert (stats.bullet_damage, stats.bullet_piercing) == (1, 0)


# --- effects ---------------------------------------------------------------

@pytest.mark.parametrize("key, changes", [
    ("faster_fire", {"shoot_interval": AUTO_SHOOT_INTERVAL * 0.80}),
    ("big_bullet", {"bullet_radius": BULLET_RADIUS + 2, "bullet_damage": 2}),
    ("thick_skin", {"invuln_time": INVULN_TIME + 0.30}),
    ("piercing_shot", {"bullet_piercing": 1}),
    ("swift_snake", {"move_interval": NORMAL * 0.90}),
])
def test_stat_upgrades_change_only_their_stats(stats, key, changes):
    new, hp = apply(key, stats, HP)
    assert hp == HP
    for field, value in vars(stats).items():
        assert getattr(new, field) == pytest.approx(changes.get(field, value)), field


def test_extra_heart_adds_hp_and_leaves_stats(stats):
    assert apply("extra_heart", stats, HP) == (stats, HP + 1)


def test_interval_upgrades_stop_at_their_floors():
    floored = Stats(move_interval=0.04, shoot_interval=0.08)
    assert apply("faster_fire", floored, HP)[0].shoot_interval == 0.08
    assert apply("swift_snake", floored, HP)[0].move_interval == 0.04


def test_upgrades_stack(stats):
    for _ in range(3):
        stats, _ = apply("piercing_shot", stats, HP)
    assert stats.bullet_piercing == 3


def test_unknown_upgrade_raises(stats):
    with pytest.raises(ValueError):
        apply("laser_eyes", stats, HP)


# --- offers & previews -----------------------------------------------------

def test_offers_are_three_distinct_upgrades():
    rng = random.Random(0)
    for _ in range(50):
        keys = [o.key for o in offers(Stats(move_interval=NORMAL), HP, rng)]
        assert len(keys) == 3 and len(set(keys)) == 3


def test_offer_carries_the_upgrades_name_and_description(stats):
    for upgrade in UPGRADES:
        o = offer(upgrade.key, stats, HP)
        assert (o.key, o.name, o.desc) == (upgrade.key, upgrade.name, upgrade.desc)


@pytest.mark.parametrize("key, preview", [
    ("faster_fire", ("Fire rate:  1.67  ->  2.08 shots/s",)),
    ("extra_heart", ("HP:  3  ->  4",)),
    ("big_bullet", ("Size:  4  ->  6 px", "Dmg:  1  ->  2")),
    ("thick_skin", ("Invuln:  0.75  ->  1.05 s",)),
    ("swift_snake", ("Speed:  10.0  ->  11.1 moves/s",)),
    ("piercing_shot", ("Pierce:  0  ->  1",)),
])
def test_preview_shows_what_picking_changes(stats, key, preview):
    assert offer(key, stats, HP).preview == preview


def test_preview_reads_the_current_stats():
    stats = Stats(move_interval=NORMAL, bullet_damage=4)
    assert offer("big_bullet", stats, HP).preview[-1] == "Dmg:  4  ->  5"


def test_preview_says_when_an_upgrade_would_change_nothing():
    floored = Stats(move_interval=NORMAL, shoot_interval=0.08)
    assert offer("faster_fire", floored, HP).preview == ("Already at its limit",)


def test_offer_for_unknown_upgrade_raises(stats):
    with pytest.raises(ValueError):
        offer("laser_eyes", stats, HP)
