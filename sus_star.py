import json
import os.path
from math import ceil, sqrt

from astar import AStar
from tqdm import tqdm

from data import Coordinates, Matrix, Circle, Route
from optimal_path import PenatyChecker, ObjectiveChecker, WidePathMutator
from precalc_base_path import OprimalPathFromBaseFinder, PathFromBaseMutator
from util import load_map, load_bags, save, cleanup_jumps_to_start, load
from checker import segment_dist, segment_time, emulate
from constants import BASE_SPEED, MAX_COORD
from itertools import product
from functools import lru_cache
from optimal_path import OptimalPathFinder

BASE_STEP = 100


@lru_cache(maxsize=65536)
def is_near_circle(node: Coordinates, buff=BASE_STEP) -> bool:
    for s in map_data.snow_areas:
        c = Circle.from_snow(s)
        c.radius += buff
        if node.in_circle(c):
            return True
    return False


@lru_cache(maxsize=65536)
def get_outside(node: Coordinates) -> Coordinates | None:
    for s in map_data.snow_areas:
        c = Circle.from_snow(s)
        if node.in_circle(c):
            return get_nearest_point_outside(c, node)
    return None


class SusStar(AStar):
    def __init__(self, goal: Coordinates):
        self.__goal = goal
        self.__goal_outside = get_outside(goal)

    def distance_between(self, n1: Coordinates, n2: Coordinates) -> float:
        d, s, _ = segment_dist(n1, n2, map_data.snow_areas)
        return segment_time(d, s)

    def neighbors(self, node: Coordinates) -> list[Coordinates]:
        result = [self.__goal] + outer
        node_outside = get_outside(node)
        if node_outside:
            result.append(node_outside)
        if self.__goal_outside:
            result.append(self.__goal_outside)
        return result

    def heuristic_cost_estimate(self, current: Coordinates, goal: Coordinates) -> float:
        return current.dist(goal) / BASE_SPEED


def expand_moves(m: list[Coordinates]) -> list[Coordinates]:
    result: list[Coordinates] = []
    prev_pos = m[0]
    for next_pos in tqdm(m[1:]):
        # prev_out = get_outside(prev_pos) or prev_pos
        # next_out = get_outside(next_pos) or next_pos
        # path = min(
        #     optimal_path(prev_pos, next_pos),
        #     [prev_pos] + optimal_path(prev_out, next_out) + [next_pos],
        #     list(SusStar(next_pos).astar(prev_pos, next_pos)),
        #     key=path_len,
        # )
        path = list(SusStar(next_pos).astar(prev_pos, next_pos))
        result.extend(path)
        prev_pos = next_pos

    return result


@lru_cache(maxsize=4096)
def optimal_path(start: Coordinates, end: Coordinates):
    return (
        OptimalPathFinder(
            max(1, int(start.dist(end) / 2_000)),
            WidePathMutator(1, 3000, 3000).mutate,
            ObjectiveChecker(penalty).objective,
            schedule={"tmax": 100, "tmin": 1, "steps": 1_000, "updates": 0},
        )
        .optimal_path(start, end)
        .path
    )


def st(n1: Coordinates, n2: Coordinates):
    d, s, _ = segment_dist(n1, n2, map_data.snow_areas)
    return segment_time(d, s)


def path_len(moves: list[Coordinates]):
    return sum(st(a, b) for a, b in zip(moves[:-1], moves[1:]))


def clamp(val, lower, upper):
    if val < lower:
        return lower
    if val > upper:
        return upper
    return val


def get_nearest_point_outside(circle: Circle, inside_pos: Coordinates):
    diff = inside_pos - circle.center
    diff = diff * (circle.radius / diff.dist(Coordinates(0, 0)))
    diff.x = ceil(diff.x)
    diff.y = ceil(diff.y)
    result = diff + circle.center
    if not result.in_bounds():
        if result.x < 0 or result.x > MAX_COORD:
            x = clamp(result.x, 0, MAX_COORD)
            y = (
                round(
                    (-1 if inside_pos.y < circle.center.y else 1)
                    * sqrt(circle.radius**2 - (circle.center.x - x) ** 2)
                )
                - circle.center.y
            )
        else:
            y = clamp(result.y, 0, MAX_COORD)
            x = (
                round(
                    (-1 if inside_pos.x < circle.center.x else 1)
                    * sqrt(circle.radius**2 - (circle.center.y - y) ** 2)
                )
                - circle.center.x
            )
        return Coordinates(x, y)
    return result


if __name__ == "__main__":
    map_data = load_map()

    circles = [Circle.from_snow(s) for s in map_data.snow_areas]
    penalty = PenatyChecker(circles).penalty
    objective = ObjectiveChecker(penalty).objective

    outer = sum(
        (Circle.from_snow(s).get_outer_points() for s in map_data.snow_areas), []
    )

    solution: Route = load(Route, "./data/solution_01GN56RWG7XD9NZZ0KF0QAB8ZC.json")
    bags = load_bags()
    solution.moves = cleanup_jumps_to_start(expand_moves(solution.moves))
    print(emulate(solution, map_data))
    save(solution, "./data/solution_vrp_star.json")
