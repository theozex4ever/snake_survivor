import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pygame
import pytest

import game as game_module
from constants import SPEED_OPTIONS
from run import Run


@pytest.fixture
def run():
    return Run(SPEED_OPTIONS[1][1], rng=random.Random(0))


@pytest.fixture
def game(tmp_path, monkeypatch):
    # An absolute path makes os.path.join ignore the source directory.
    monkeypatch.setattr(game_module, "HIGH_SCORE_FILE", str(tmp_path / "highscore.txt"))
    g = game_module.Game()
    g.sound_mgr.play = lambda name: None
    g._start_run()
    g.run = Run(g.run.stats.move_interval, rng=random.Random(0))  # seeded for repeatable tests
    yield g
    pygame.quit()
