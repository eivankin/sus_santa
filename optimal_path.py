from dataclasses import dataclass
from random import gauss, uniform
import warnings
from data import Circle, Coordinates, Line, Path, Route
from simanneal import Annealer

from util import load_map
from visualizer import visualize_route


@dataclass
class PenatyChecker:
    circles: list[Circle]

    def penalty(self, f: Coordinates, t: Coordinates) -> float:
        # context unaware
        l = Line.from_two_points(f, t)
        return sum(l.distance_in_circle(s) for s in self.circles)


@dataclass
class ObjectiveChecker:
    penalty: callable

    def objective(self, path: list[Coordinates]):
        # TODO: optimize:
        # write is_len_smaller(path, len) instead
        # that returns the actual len of the path only in case when it is smaller,
        # so it can throw summation of path pieces if it finds that the sum is already bigger that the threshold

        # context unaware
        res = 0
        prev = path[0]
        for pos in path[1:]:
            res += prev.dist(pos) + 6 * self.penalty(pos, prev)
            prev = pos
        return res


# TODO: mutators that use coordinate system rotation (they converge very fast)


@dataclass
class CrazyPathMutator:
    threshold: float

    def mutate(self, path: list[Coordinates], *_) -> list[Coordinates]:
        return [
            Coordinates(uniform(0, 10000), uniform(0, 10000))
            if uniform(0, 1) < self.threshold
            else c
            for c in path
        ]


@dataclass
class WidePathMutator:
    threshold: float
    x_var: float
    y_var: float

    def mutate(self, path: list[Coordinates], *_) -> list[Coordinates]:
        return [
            Coordinates(
                min(max(gauss(c.x, self.x_var), 0), 10000),
                min(max(gauss(c.y, self.y_var), 0), 10000),
            )
            if uniform(0, 1) < self.threshold
            else c
            for c in path
        ]


# TODO: coordinate system aware rand_path_generator (makes convergence faster)


def absolute_rand_path(segmentation, *_):
    res = [None] * segmentation
    for i in range(segmentation):
        res[i] = Coordinates(uniform(0, 10000), uniform(0, 10000))
    return res


# a generalization of just a base path finder
class OptimalPathFinder:
    segmentation: int
    mutate: callable  # context aware
    objective: callable  # context unaware
    rand_path_generator: callable  # context aware
    schedule: dict = {"tmax": 100.0, "tmin": 1, "steps": 340, "updates": 100}

    def __init__(
        self,
        segmentation,
        mutate,
        objective,
        rand_path_generator=None,
        schedule=None,
    ):
        self.segmentation = segmentation
        self.mutate = mutate
        self.objective = objective
        if rand_path_generator is None:
            self.rand_path_generator = absolute_rand_path
        else:
            self.rand_path_generator = rand_path_generator
        if schedule is not None:
            self.schedule = schedule

    def optimal_path(self, f: Coordinates, t: Coordinates) -> Path:
        mutate = self.mutate
        objective = self.objective

        l = f.dist(t)
        if l < 200:
            return Path([f, t], objective([f, t]))

        cos_a = f.x / l
        sin_a = f.y / l

        class PathAnnealer(Annealer):
            def move(self):
                path = [f] + mutate(self.state.path[1:-1], cos_a, sin_a, l) + [t]
                length = objective(path)
                self.state = Path(path, length)

            def energy(self):
                return self.state.length

        init = [f] + self.rand_path_generator(self.segmentation, cos_a, sin_a, l) + [t]
        annealer = PathAnnealer(Path(init, objective(init)))
        annealer.set_schedule(self.schedule)
        best, cost = annealer.anneal()
        linear = Path([f, t], objective([f, t]))
        if cost > linear.length:
            return linear
        # NOTE: assuming int rounding does not change path len significantly
        return Path([Coordinates(int(c.x), int(c.y)) for c in best.path], cost)


def main():
    warnings.filterwarnings("ignore")
    a = Coordinates.from_str(input("Enter a: "))
    b = Coordinates.from_str(input("Enter b: "))
    sengemtation = int(input("Enter number of segments: "))

    sus_map = load_map()
    circles = [Circle.from_snow(s) for s in sus_map.snow_areas]
    penalty = PenatyChecker(circles).penalty

    print("linear: ", a.dist(b) + 6 * penalty(a, b))
    best = OptimalPathFinder(
        sengemtation,
        WidePathMutator(1, 3000, 3000).mutate,
        ObjectiveChecker(penalty).objective,
        schedule={"tmax": 100, "tmin": 1, "steps": 500, "updates": 500},
    ).optimal_path(a, b)

    print()
    if input("draw? (y/n): ") == "y":
        visualize_route(sus_map, Route(best.path, None, None)).save("data/path.png")


if __name__ == "__main__":
    main()
