"""Headless bot playtester.

Plays full runs of the real `Run` at a fixed 60 FPS timestep, then reports how runs end and how waves/upgrades behave. Intended
to surface balance and fairness problems that unit tests cannot.

    python tools/playtest.py --runs 30 --speed Normal --profile careful
"""
import argparse
import json
import os
import random
import statistics
import sys
from collections import Counter, deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import GRID_HEIGHT, GRID_WIDTH, SPEED_OPTIONS, CELL_SIZE  # noqa: E402
from run import FoodEaten, Run  # noqa: E402

DT = 1 / 60
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
MAX_SIM_SECONDS = 600


def in_bounds(c):
    return 0 <= c[0] < GRID_WIDTH and 0 <= c[1] < GRID_HEIGHT


def danger_cells(run, radius_px):
    """Grid cells within radius_px of a living enemy."""
    cells = set()
    r = int(radius_px // CELL_SIZE) + 1
    for e in run.enemies:
        cx, cy = int(e.pos.x // CELL_SIZE), int(e.pos.y // CELL_SIZE)
        for x in range(cx - r, cx + r + 1):
            for y in range(cy - r, cy + r + 1):
                if in_bounds((x, y)) and (
                    (x + 0.5) * CELL_SIZE - e.pos.x) ** 2 + ((y + 0.5) * CELL_SIZE - e.pos.y) ** 2 <= radius_px ** 2:
                    cells.add((x, y))
    return cells


def bfs_first_step(start, goal, blocked):
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            while prev[cur] != start and prev[cur] is not None:
                cur = prev[cur]
            return (cur[0] - start[0], cur[1] - start[1])
        for d in DIRS:
            n = (cur[0] + d[0], cur[1] + d[1])
            if n not in prev and in_bounds(n) and n not in blocked:
                prev[n] = cur
                q.append(n)
    return None


def choose_direction(run, profile):
    snake = run.snake
    head = snake.head
    body = set(snake.segments[:-1])
    cur = snake.direction
    reverse = (-cur[0], -cur[1])
    blocked_sets = [body]
    if profile == "careful":
        blocked_sets.insert(0, body | danger_cells(run, 70))
    for blocked in blocked_sets:
        step = bfs_first_step(head, run.food, blocked - {head})
        if step and step != reverse:
            return step
    # No path: take any safe move, preferring the one with most open neighbours.
    best, best_score = None, -1
    for d in DIRS:
        n = (head[0] + d[0], head[1] + d[1])
        if d == reverse or not in_bounds(n) or n in body:
            continue
        score = sum(1 for dd in DIRS if in_bounds((n[0] + dd[0], n[1] + dd[1])) and (n[0] + dd[0], n[1] + dd[1]) not in body)
        if score > best_score:
            best, best_score = d, score
    return best


def death_cause(run, hp_before):
    s = run.snake
    if s.hp <= 0 and s.hp < hp_before:
        return "enemy"
    hx, hy = s.head
    dx, dy = s.direction
    return "wall" if not in_bounds((hx + dx, hy + dy)) else "self"


def advance(run):
    """Run one frame; return (hit, ate) as 0/1 counts for HP loss and food pickup."""
    hp_before = run.snake.hp
    events = run.step(DT)
    return int(run.snake.hp < hp_before), sum(isinstance(e, FoodEaten) for e in events)


def play_run(speed_index, profile, upgrade_policy, seed):
    run = Run(SPEED_OPTIONS[speed_index][1], rng=random.Random(seed))
    rng = random.Random(f"upgrade-policy-{seed}")
    t = 0.0
    upgrades = []
    hits = 0
    wave_times = {}
    foods = 0
    last_wave_start = 0.0
    while t < MAX_SIM_SECONDS:
        if run.phase == "choosing_upgrade":
            offers = run.offers
            if upgrade_policy == "first":
                key = offers[0].key
            elif upgrade_policy.startswith("prefer:"):
                wanted = upgrade_policy.split(":", 1)[1]
                key = wanted if any(o.key == wanted for o in offers) else rng.choice(offers).key
            else:
                key = rng.choice(offers).key
            upgrades.append(key)
            wave_times[run.wave] = t - last_wave_start
            last_wave_start = t
            run.pick_upgrade(key)
            continue
        # Decide once per move, just before it happens.
        if run.time_to_next_move <= DT and not run.snake.direction_queue:
            d = choose_direction(run, profile)
            if d:
                run.steer(d)
        hp_before = run.snake.hp
        hit, ate = advance(run)
        t += DT
        hits += hit
        foods += ate
        if run.phase == "over":
            return dict(cause=death_cause(run, hp_before), wave=run.wave, score=run.score,
                        seconds=round(t, 1), upgrades=upgrades, hits=hits, foods=foods,
                        wave_times=wave_times, length=len(run.snake.segments))
    return dict(cause="survived", wave=run.wave, score=run.score, seconds=round(t, 1),
                upgrades=upgrades, hits=hits, foods=foods, wave_times=wave_times,
                length=len(run.snake.segments))


def summarize(results):
    n = len(results)
    causes = Counter(r["cause"] for r in results)
    waves = [r["wave"] for r in results]
    return {
        "runs": n,
        "causes": dict(causes),
        "wave_median": statistics.median(waves),
        "wave_max": max(waves),
        "wave_min": min(waves),
        "score_median": statistics.median(r["score"] for r in results),
        "seconds_median": statistics.median(r["seconds"] for r in results),
        "hits_median": statistics.median(r["hits"] for r in results),
        "foods_median": statistics.median(r["foods"] for r in results),
        "upgrade_picks": dict(Counter(u for r in results for u in r["upgrades"])),
        "died_before_wave_3_pct": round(100 * sum(w < 3 for w in waves) / n, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--speed", default="Normal", choices=[n for n, _ in SPEED_OPTIONS])
    ap.add_argument("--profile", default="careful", choices=["greedy", "careful"])
    ap.add_argument("--upgrades", default="random",
                    help="random | first | prefer:<upgrade key> (take that upgrade whenever offered)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--json", help="write raw results to this path")
    args = ap.parse_args()

    idx = [n for n, _ in SPEED_OPTIONS].index(args.speed)

    results = []
    for i in range(args.runs):
        results.append(play_run(idx, args.profile, args.upgrades, args.seed * 1000 + i))
    summary = summarize(results)
    summary.update(speed=args.speed, profile=args.profile, upgrades=args.upgrades, seed=args.seed)
    print(json.dumps(summary, indent=2))
    if args.json:
        with open(args.json, "w") as f:
            json.dump({"summary": summary, "runs": results}, f, indent=1)


if __name__ == "__main__":
    main()
