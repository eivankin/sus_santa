import visualizer
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
    SnowArea,
)
from constants import BAG_MAX_WEIGHT, BAG_MAX_VOLUME, BASE_SPEED, SNOW_SPEED, IDS_FILE
from util import (
    save,
    load,
    load_map,
    send_solution,
    get_solution_info,
    edit_json_file,
    cleanup_jumps_to_start,
    segment_dist,
    segment_time
)


def is_bag_valid(bag: BagDescription) -> bool:
    return bag.weight <= BAG_MAX_WEIGHT and bag.volume <= BAG_MAX_VOLUME


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
    for next_pos in solution.moves + [None]:
        assert curr_pos.in_bounds()

        if curr_bag and curr_pos in children:
            curr_bag.pop()

        if not curr_bag and curr_pos == start:
            curr_bag = bags.pop().copy()

        if next_pos is None:
            break

        dist, snow_dist, distances_in_snow = segment_dist(
            curr_pos, next_pos, map_data.snow_areas
        )
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

    sol: Route = load(Route, "data/solution_vrp.json")
    mp = load_map()
    print(emulate(sol, mp))
    print(len(sol.moves))
    visualizer.visualize_route(mp, sol).save("./data/route.png")
    if input("Send solution? y/n: ").lower() in ("y", "yes"):
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
