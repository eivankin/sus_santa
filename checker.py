from data import Route, BagDescription, Map, Coordinates, RouteData, Line, Circle, EmulatorReport, \
    EmulatorReportSegment
from constants import BAG_MAX_WEIGHT, BAG_MAX_VOLUME, BASE_SPEED, SNOW_SPEED
from util import save


def is_bag_valid(bag: BagDescription) -> bool:
    return bag.weight <= BAG_MAX_WEIGHT and bag.volume <= BAG_MAX_VOLUME


def emulate(solution: Route, map_data: Map) -> RouteData:
    gifts = sum(solution.stack_of_bags, [])
    assert sorted(gifts) == [*range(1, len(map_data.children) + 1)], \
        'List of gifts mismatches list of children'

    for i, bag in enumerate(solution.stack_of_bags):
        assert is_bag_valid(BagDescription.from_bag(map_data, bag)), f'Bag #{i} {bag} is too big'

    start = Coordinates(0, 0)
    children = set(map_data.children)
    bags = solution.stack_of_bags.copy()
    curr_pos = start
    curr_bag = bags.pop()

    total_dist = 0
    total_time = 0
    segments: list[EmulatorReportSegment] = []
    tot_snow = 0
    for next_pos in solution.moves:
        if curr_bag and curr_pos in children:
            curr_bag.pop()

        if not curr_bag and curr_pos == start:
            curr_bag = bags.pop()

        dist = curr_pos.dist(next_pos)
        total_dist += dist
        line = Line.from_two_points(curr_pos, next_pos)
        distances_in_snow = [line.distance_in_circle(Circle.from_snow(snow))
                             for snow in map_data.snow_areas]
        snow_dist = sum(distances_in_snow)
        tot_snow += snow_dist
        assert snow_dist <= dist
        total_time += snow_dist / SNOW_SPEED + (dist - snow_dist) / BASE_SPEED
        segments.append(EmulatorReportSegment(distances_in_snow=distances_in_snow, from_pos=curr_pos, to_pos=next_pos, distance=dist))
        curr_pos = next_pos

    assert not curr_bag
    assert not bags

    save(EmulatorReport(segments=segments, total_distance=total_dist, distance_in_snow=tot_snow),
         './data/report.json')

    return RouteData('', 'Checker verdict', round(total_time), round(total_dist))
