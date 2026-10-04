# TECH-003: Food placement loops forever on a full grid

| | |
| --- | --- |
| Severity | Low (unreachable in practice: the grid has 1,600 cells) |
| Category | Technical (software defect) |
| Area | Utils / `utils.py` |
| Status | Fixed |
| Branch | `docs/setup-agent-skills` |
| Found by | Code review; confirmed by a test that hangs on the original code |
| Fixed in | `utils.py` |

## Summary
`random_empty_cell` retried random cells in a `while True` loop. If every cell was occupied it never returned.

## Root cause
Rejection sampling with no termination guarantee. It also slows down as the snake fills the grid.

## Fix
Build the list of free cells and `random.choice` from it. Raise `ValueError` if the list is empty. This is O(cells), which is trivial at this grid size.

## Regression test
`tests/test_systems.py::test_random_empty_cell_full_grid_raises` (on the original code this test never finishes)
