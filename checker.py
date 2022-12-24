from data import (
    Route,
    BagDescription,
    Map,
    Coordinates,
    RouteData,
    Line,
    Circle,
    EmulatorReport,
    EmulatorReportSegment,
    SnowArea
)
from constants import BAG_MAX_WEIGHT, BAG_MAX_VOLUME, BASE_SPEED, SNOW_SPEED, IDS_FILE
from util import save, load, load_map, send_solution, get_solution_info, edit_json_file


def is_bag_valid(bag: BagDescription) -> bool:
    return bag.weight <= BAG_MAX_WEIGHT and bag.volume <= BAG_MAX_VOLUME


def segment_dist(from_pos: Coordinates, to_pos: Coordinates,
                 snow_areas: list[SnowArea]) -> tuple[float, float, list[float]]:
    dist = from_pos.dist(to_pos)
    line = Line.from_two_points(from_pos, to_pos)
    distances_in_snow = [
        line.distance_in_circle(Circle.from_snow(snow))
        for snow in snow_areas
    ]
    snow_dist = sum(distances_in_snow)
    assert snow_dist <= dist
    return dist, snow_dist, distances_in_snow


def segment_time(dist: float, snow_dist: float) -> float:
    return snow_dist / SNOW_SPEED + (dist - snow_dist) / BASE_SPEED


def emulate(solution: Route, map_data: Map) -> RouteData:
    gifts = sum(solution.stack_of_bags, [])
    assert sorted(gifts) == [
        *range(1, len(map_data.children) + 1)
    ], "List of gifts mismatches list of children"

    for i, bag in enumerate(solution.stack_of_bags):
        assert is_bag_valid(
            BagDescription.from_bag(map_data, bag)
        ), f"Bag #{i} {bag} is too big"

    start = Coordinates(0, 0)
    children = set(map_data.children)
    bags = solution.stack_of_bags.copy()
    curr_pos = start
    curr_bag = bags.pop().copy()

    total_dist = 0
    total_time = 0
    segments: list[EmulatorReportSegment] = []
    tot_snow = 0
    for next_pos in solution.moves:
        if curr_bag and curr_pos in children:
            curr_bag.pop()

        if not curr_bag and curr_pos == start:
            curr_bag = bags.pop().copy()

        dist, snow_dist, distances_in_snow = segment_dist(curr_pos, next_pos, map_data.snow_areas)
        assert dist > 0
        total_dist += dist
        tot_snow += snow_dist
        total_time += segment_time(dist, snow_dist)
        segments.append(
            EmulatorReportSegment(
                distances_in_snow=distances_in_snow,
                from_pos=curr_pos,
                to_pos=next_pos,
                distance=dist,
            )
        )
        curr_pos = next_pos

    assert not curr_bag
    assert not bags

    save(
        EmulatorReport(
            segments=segments, total_distance=total_dist, distance_in_snow=tot_snow
        ),
        "./data/report.json",
    )

    return RouteData("", "Checker verdict", round(total_time), round(total_dist))


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    sol: Route = load(Route, "./data/solution_vrp.json")
    moves = [Coordinates(0, 0)]
    for c in sol.moves:
        if c != moves[-1]:
            moves.append(c)

    sol.moves = moves[1:]
    mp = load_map()
    print(emulate(sol, mp))
    sus_response = send_solution(sol)
    print("=== RESPONSE ===")
    print(sus_response)
    print("=== INFO ===")
    if sus_response.success:
        print(get_solution_info(sus_response.round_id))
        with edit_json_file(IDS_FILE) as solution:
            solution[sus_response.round_id] = input("label: ")
    else:
        print("Unsuccessful")
