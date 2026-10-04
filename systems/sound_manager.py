"""Sound manager for Snake Shooter.

Loads .wav files from assets/sfx/, generates them procedurally if missing.
Uses pygame.mixer for playback; degrades gracefully if mixer is unavailable.
"""

import array
import math
import os
import wave

MASTER_VOLUME = 0.6

RATE = 22050  # Hz, 16-bit signed mono PCM


# ---------------------------------------------------------------------------
# WAV generation helpers
# ---------------------------------------------------------------------------

def _write_wav(path: str, samples: list, rate: int = RATE) -> None:
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)  # 16-bit
        f.setframerate(rate)
        data = array.array("h", samples)
        f.writeframes(data.tobytes())


def _clamp(value: int) -> int:
    return max(-32767, min(32767, value))


def _sine_samples(
    freq: float,
    duration: float,
    rate: int = RATE,
    amplitude: float = 0.6,
    decay: float = 1.0,
) -> list:
    """Sine wave with exponential amplitude decay."""
    n = int(rate * duration)
    return [
        _clamp(int(
            amplitude * 32767
            * math.sin(2 * math.pi * freq * i / rate)
            * math.exp(-decay * i / n)
        ))
        for i in range(n)
    ]


def _sweep_samples(
    freq_start: float,
    freq_end: float,
    duration: float,
    rate: int = RATE,
    amplitude: float = 0.6,
    decay: float = 1.0,
) -> list:
    """Sine wave that linearly sweeps frequency, with exponential decay."""
    n = int(rate * duration)
    samples = []
    phase = 0.0
    for i in range(n):
        t = i / n  # 0 → 1
        freq = freq_start + (freq_end - freq_start) * t
        env = math.exp(-decay * t)
        samples.append(_clamp(int(amplitude * 32767 * math.sin(phase) * env)))
        phase += 2 * math.pi * freq / rate
    return samples


def _vibrato_samples(
    freq: float,
    duration: float,
    vibrato_rate: float = 8.0,
    vibrato_depth: float = 0.03,
    rate: int = RATE,
    amplitude: float = 0.55,
    decay: float = 0.6,
) -> list:
    """Buzzy sine with vibrato modulation."""
    n = int(rate * duration)
    samples = []
    phase = 0.0
    for i in range(n):
        t = i / n
        mod_freq = freq * (1.0 + vibrato_depth * math.sin(2 * math.pi * vibrato_rate * i / rate))
        env = math.exp(-decay * t)
        samples.append(_clamp(int(amplitude * 32767 * math.sin(phase) * env)))
        phase += 2 * math.pi * mod_freq / rate
    return samples


def generate_sfx(sfx_dir: str) -> None:
    """Create procedural WAV files in sfx_dir if they don't already exist."""
    os.makedirs(sfx_dir, exist_ok=True)

    files = {
        # shoot.wav — 120ms high-pitched descending chirp 800→400 Hz
        "shoot.wav": lambda: _sweep_samples(800, 400, 0.12, amplitude=0.55, decay=3.0),

        # hit_enemy.wav — 100ms mid-frequency thud at 250 Hz, sharp attack
        "hit_enemy.wav": lambda: _sweep_samples(250, 180, 0.10, amplitude=0.65, decay=4.0),

        # kill_enemy.wav — 180ms satisfying pop: 500→80 Hz
        "kill_enemy.wav": lambda: _sweep_samples(500, 80, 0.18, amplitude=0.70, decay=2.5),

        # player_hurt.wav — 250ms low buzzy warning at 120 Hz with vibrato
        "player_hurt.wav": lambda: _vibrato_samples(
            120, 0.25, vibrato_rate=10.0, vibrato_depth=0.06, amplitude=0.65, decay=0.8
        ),

        # eat_food.wav — 80ms pleasant rising blip 400→900 Hz
        "eat_food.wav": lambda: _sweep_samples(400, 900, 0.08, amplitude=0.55, decay=2.0),

        # wave_complete.wav — 500ms ascending arpeggio: 300→375→450→600 Hz (each ~120ms)
        "wave_complete.wav": lambda: (
            _sine_samples(300, 0.12, amplitude=0.55, decay=2.5)
            + _sine_samples(375, 0.12, amplitude=0.55, decay=2.5)
            + _sine_samples(450, 0.12, amplitude=0.55, decay=2.5)
            + _sine_samples(600, 0.14, amplitude=0.60, decay=2.0)
        ),

        # game_over.wav — 600ms three descending notes: 400→280→200 Hz (each ~180ms)
        "game_over.wav": lambda: (
            _sine_samples(400, 0.18, amplitude=0.60, decay=2.0)
            + _sine_samples(280, 0.18, amplitude=0.60, decay=2.0)
            + _sine_samples(200, 0.24, amplitude=0.65, decay=1.5)
        ),
    }

    for filename, gen in files.items():
        path = os.path.join(sfx_dir, filename)
        if not os.path.exists(path):
            _write_wav(path, gen())


# ---------------------------------------------------------------------------
# SoundManager
# ---------------------------------------------------------------------------

class SoundManager:
    """Loads and plays sound effects via pygame.mixer.

    Degrades gracefully if pygame.mixer is unavailable or SDL audio fails.
    """

    def __init__(self) -> None:
        self._sounds: dict = {}
        self._muted: bool = False
        self._mixer_ok: bool = False

    # ------------------------------------------------------------------
    def load(self) -> None:
        """Initialise mixer, generate WAV assets if needed, then load them."""
        # Locate assets/sfx/ relative to this file's package root
        here = os.path.dirname(os.path.abspath(__file__))
        package_root = os.path.dirname(here)  # …/snake_survivor/
        sfx_dir = os.path.join(package_root, "assets", "sfx")

        # Always generate missing WAV files (uses only stdlib)
        generate_sfx(sfx_dir)

        # Try to initialise pygame.mixer
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=512)
            self._mixer_ok = True
        except Exception:
            # mixer unavailable (headless, no audio device, etc.) — silent mode
            self._mixer_ok = False
            return

        # Load every WAV from sfx_dir
        for filename in os.listdir(sfx_dir):
            if filename.lower().endswith(".wav"):
                name = filename[:-4]  # strip .wav
                path = os.path.join(sfx_dir, filename)
                try:
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(MASTER_VOLUME)
                    self._sounds[name] = sound
                except Exception:
                    pass  # skip unreadable files silently

    # ------------------------------------------------------------------
    def play(self, name: str) -> None:
        """Play sound by name. Silently skips if muted, not loaded, or unknown."""
        if self._muted or not self._mixer_ok:
            return
        sound = self._sounds.get(name)
        if sound is not None:
            sound.play()

    # ------------------------------------------------------------------
    def toggle_mute(self) -> None:
        """Toggle mute on/off."""
        self._muted = not self._muted

    # ------------------------------------------------------------------
    @property
    def is_muted(self) -> bool:
        """Return current mute state."""
        return self._muted
