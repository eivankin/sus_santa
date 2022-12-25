import argparse
from dataclasses import dataclass
import json
from random import gauss, uniform
from data import Circle, Coordinates, Line, Path, Route
from util import edit_json_file, load_map, read_json_file
from simanneal import Annealer
from constants import PRECALC_BASE_FILE
from visualizer import visualize_route
from tqdm import tqdm
from optimal_path import WidePathMutator, ObjectiveChecker, PenatyChecker

import warnings

base = Coordinates(0, 0)


def translate(pos: Coordinates, cos_a, sin_a) -> Coordinates:
    # represent back from the rotated coordinate system
    return Coordinates(
        pos.x * cos_a - pos.y * sin_a,
        pos.x * sin_a + pos.y * cos_a,
    )


def retranslate(pos: Coordinates, cos_a, sin_a) -> Coordinates:
    # represent in the rotated coordinate system
    return Coordinates(
        pos.x * cos_a + pos.y * sin_a,
        pos.y * cos_a - pos.x * sin_a,
    )


def rand_path_from_base(segmentation, cos_a, sin_a, l):
    # context aware
    res = [None] * segmentation
    for i in range(segmentation):
        x = l * (i + 1) / (segmentation + 1)
        y_max = min(x * cos_a / sin_a, (10000 - x * sin_a) / cos_a)
        y_min = max(-x * sin_a / cos_a, (-10000 + x * cos_a) / sin_a)
        y = uniform(y_min, y_max)
        res[i] = translate(Coordinates(x, y), cos_a, sin_a)
    return res


def straight_path_from_base(segmentation, cos_a, sin_a, l):
    # context aware
    res = [None] * segmentation
    for i in range(segmentation):
        x = l * (i + 1) / (segmentation + 1)
        y = 0
        res[i] = translate(Coordinates(x, y), cos_a, sin_a)
    return res


@dataclass
class PathFromBaseMutator:
    x_var: int
    y_var: int

    def mutate(self, path: list[Coordinates], cos_a, sin_a, l) -> list[Coordinates]:
        # context aware
        mutant = [0] * len(path)
        # knowing the constext of [base, *path, f]
        rpath = [Coordinates(10, 0)]
        rpath.extend(retranslate(pos, cos_a, sin_a) for pos in path)
        rpath.append(Coordinates(l - 10, 0))
        for i, p in enumerate(rpath[1:-1]):
            x_max = rpath[i + 2].x - 1
            x_min = rpath[i].x + 1
            if x_max > x_min:
                p.x = gauss(p.x, self.x_var)
                p.x = max(x_min, min(x_max, p.x))
            y_max = min(p.x * cos_a / sin_a, (10000 - p.x * sin_a) / cos_a)
            y_min = max(-p.x * sin_a / cos_a, (-10000 + p.x * cos_a) / sin_a)
            p.y = gauss(p.y, self.y_var)
            p.y = max(y_min, min(y_max, p.y))
            mutant[i] = translate(p, cos_a, sin_a)
        return mutant


class OprimalPathFromBaseFinder:
    segmentation: int
    mutate: callable  # context aware
    objective: callable  # context unaware
    rand_path_from_base: callable  # context aware
    schedule: dict = {"tmax": 100.0, "tmin": 1, "steps": 340, "updates": 100}

    def __init__(
        self,
        segmentation,
        mutate,
        objective,
        rand_path_from_base_generator=None,
        schedule=None,
    ):
        self.segmentation = segmentation
        self.mutate = mutate
        self.objective = objective
        if rand_path_from_base_generator is None:
            self.rand_path_from_base = rand_path_from_base
        else:
            self.rand_path_from_base = rand_path_from_base_generator
        if schedule is not None:
            self.schedule = schedule

    def optimal_path(self, f: Coordinates) -> Path:
        mutate = self.mutate
        objective = self.objective

        l = f.dist(base)
        if l < 200:
            return Path([base, f], objective([base, f]))

        cos_a = f.x / l
        sin_a = f.y / l

        class PathAnnealer(Annealer):
            def move(self):
                path = [base] + mutate(self.state.path[1:-1], cos_a, sin_a, l) + [f]
                length = objective(path)
                self.state = Path(path, length)

            def energy(self):
                return self.state.length

        init = (
            [base] + self.rand_path_from_base(self.segmentation, cos_a, sin_a, l) + [f]
        )
        annealer = PathAnnealer(Path(init, objective(init)))
        annealer.set_schedule(self.schedule)
        best, cost = annealer.anneal()
        linear = Path([base, f], objective([base, f]))
        if cost > linear.length:
            return linear
        # NOTE: assuming int rounding does not change path len significantly
        return Path([Coordinates(int(c.x), int(c.y)) for c in best.path], cost)


def main():
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--point", type=Coordinates.from_str)
    parser.add_argument("-i", "--index", type=int)
    parser.add_argument("-b", "--bunch", action="store_true")
    parser.add_argument("-a", "--all_children", action="store_true")
    parser.add_argument("-v", "--visualize", action="store_true")
    args = parser.parse_args()

    sus_map = load_map()

    circles = [Circle.from_snow(s) for s in sus_map.snow_areas]
    penalty = PenatyChecker(circles).penalty
    objective = ObjectiveChecker(penalty).objective

    silent = False

    def optimal_path(f: Coordinates) -> Path:
        segmentation = int(f.dist(base) // 2000)
        return OprimalPathFromBaseFinder(
            segmentation,
            PathFromBaseMutator(2000, 2000).mutate,
            # WidePathMutator(1, 3000, 3000).mutate,
            objective,
            schedule={
                "tmax": 100,
                "tmin": 1,
                "steps": 500,
                "updates": 500 if not silent else 0,
            },
        ).optimal_path(f)

    if args.all_children:
        improved = 0
        created = 0
        silent = True
        with edit_json_file(PRECALC_BASE_FILE) as precalc:
            for p in tqdm(sus_map.children):
                best = optimal_path(p)
                p = p.to_str()
                if p not in precalc or Path.from_dict(precalc[p]).length > best.length:
                    if p in precalc:
                        improved += 1
                    else:
                        created += 1
                    precalc[p] = best.to_dict()
        print(
            f"improved: {improved}/{len(sus_map.children)}, created: {created}/{len(sus_map.children)}"
        )
        return

    if args.bunch:
        improved = 0
        created = 0
        silent = True
        print("enter points: ")
        points = json.loads(input())
        with edit_json_file(PRECALC_BASE_FILE) as precalc:
            for p in tqdm(points):
                best = optimal_path(Coordinates.from_str(p))
                if p not in precalc or Path.from_dict(precalc[p]).length > best.length:
                    if p in precalc:
                        improved += 1
                    else:
                        created += 1
                    precalc[p] = best.to_dict()
        print(
            f"improved: {improved}/{len(points)}, created: {created}/{len(points)}"
        )
        return

    if args.point is None:
        args.point = sus_map.children[args.index]

    k = args.point.to_str()
    if args.visualize:
        with read_json_file(PRECALC_BASE_FILE) as res:
            if k not in res:
                print("No such point")
            else:
                path = Path.from_dict(res[k])
                print(
                    "objective:",
                    path.length,
                )
                print("path:", path.path[1:-1])
                if input("draw? (y/n): ") == "y":
                    visualize_route(sus_map, Route(path.path, None, None)).save(
                        "data/path.png"
                    )
    else:
        print("linear: ", base.dist(args.point) + 6 * penalty(base, args.point))
        with read_json_file(PRECALC_BASE_FILE) as res:
            if k not in res:
                print("no previous results")
            else:
                print("best: ", Path.from_dict(res[k]).length)

        best_path = optimal_path(args.point)

        with edit_json_file(PRECALC_BASE_FILE) as res:
            old = Path.from_dict(res[k])
            if k not in res or old.length > best_path.length:
                res[k] = best_path.to_dict()

        print()
        if input("draw? (y/n): ") == "y":
            visualize_route(sus_map, Route(best_path.path, None, None)).save(
                "data/path.png"
            )


if __name__ == "__main__":
    main()
