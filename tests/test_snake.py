from constants import GRID_HEIGHT, GRID_WIDTH, INITIAL_SNAKE_LENGTH, STARTING_PLAYER_HP
from entities import Snake


def test_starts_centered_moving_right():
    s = Snake()
    assert len(s.segments) == INITIAL_SNAKE_LENGTH
    assert s.head == (GRID_WIDTH // 2, GRID_HEIGHT // 2)
    assert s.direction == (1, 0)
    assert s.hp == STARTING_PLAYER_HP


def test_move_advances_head_and_keeps_length():
    s = Snake()
    head = s.head
    s.move()
    assert s.head == (head[0] + 1, head[1])
    assert len(s.segments) == INITIAL_SNAKE_LENGTH


def test_grow_extends_over_next_move():
    s = Snake()
    s.grow(2)
    s.move()
    s.move()
    s.move()
    assert len(s.segments) == INITIAL_SNAKE_LENGTH + 2


def test_reverse_is_blocked():
    s = Snake()
    s.set_direction((-1, 0))
    s.move()
    assert s.direction == (1, 0)


def test_turns_are_buffered_across_moves():
    s = Snake()
    s.set_direction((0, -1))
    s.set_direction((-1, 0))  # up then left within one tick
    head = s.head
    s.move()
    assert s.head == (head[0], head[1] - 1)
    s.move()
    assert s.head == (head[0] - 1, head[1] - 1)


def test_reversal_checked_against_queued_direction():
    s = Snake()
    s.set_direction((0, -1))
    s.set_direction((0, 1))  # would reverse the queued "up"
    assert s.direction_queue == [(0, -1)]


def test_duplicate_direction_not_queued():
    s = Snake()
    s.set_direction((1, 0))
    assert s.direction_queue == []


def test_queue_is_capped():
    s = Snake()
    for d in [(0, -1), (-1, 0), (0, 1), (1, 0)]:
        s.set_direction(d)
    assert len(s.direction_queue) == 2


def test_wall_collision_kills():
    s = Snake()
    s.segments = [(GRID_WIDTH - 1, 5), (GRID_WIDTH - 2, 5)]
    s.move()
    assert not s.alive


def test_self_collision_kills():
    s = Snake()
    s.segments = [(5, 5), (5, 6), (4, 6), (4, 5), (4, 4), (5, 4), (6, 4)]
    s.direction = (0, -1)
    s.direction_queue = [(-1, 0)]  # head (5,5) -> (4,5), a body cell
    s.move()
    assert not s.alive


def test_moving_into_vacating_tail_is_safe():
    s = Snake()
    # 2x2 loop: head chases its own tail.
    s.segments = [(5, 5), (5, 6), (6, 6), (6, 5)]
    s.direction = (0, -1)
    s.direction_queue = [(1, 0)]  # head -> (6,5), the tail cell
    s.move()
    assert s.alive


def test_moving_into_tail_while_growing_kills():
    s = Snake()
    s.segments = [(5, 5), (5, 6), (6, 6), (6, 5)]
    s.direction = (0, -1)
    s.direction_queue = [(1, 0)]
    s.grow(1)
    s.move()
    assert not s.alive


def test_damage_costs_hp_and_a_segment_then_grants_invulnerability():
    s = Snake()
    s.take_damage(1, 0.5)
    assert s.hp == STARTING_PLAYER_HP - 1
    assert len(s.segments) == INITIAL_SNAKE_LENGTH - 1
    s.take_damage(1, 0.5)  # ignored while invulnerable
    assert s.hp == STARTING_PLAYER_HP - 1


def test_invulnerability_expires():
    s = Snake()
    s.take_damage(1, 0.5)
    s.update(0.6)
    assert s.can_take_damage()


def test_snake_never_shrinks_below_one_segment():
    s = Snake()
    s.segments = [(5, 5)]
    s.take_damage(1, 0.0)
    assert len(s.segments) == 1


def test_zero_hp_kills():
    s = Snake()
    s.hp = 1
    s.take_damage(1, 0.5)
    assert not s.alive
