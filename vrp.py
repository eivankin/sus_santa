"""Capacited Vehicles Routing Problem (CVRP)."""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from tqdm import tqdm

import json
import os
from math import sqrt, ceil

from data import Map, Bag, Coordinates, SnowArea, Route, Circle, Matrix, Path
from util import load_map, load_bags, save, cleanup_jumps_to_start, path_len
from checker import segment_dist, segment_time
from constants import BASE_SPEED, TIMES_MATRIX_PATH, MAP_ID, PRECALC_BASE_FILE
from copy import deepcopy

from visualizer import visualize_route


def update_matrix(matrix: Matrix, vertices: list[Coordinates]) -> Matrix:
    result = deepcopy(matrix)
    i = 0
    with open(PRECALC_BASE_FILE, "r") as inp:
        pb = json.load(inp)
        for j in range(1, len(matrix)):
            result[i][j] = result[j][i] = (
                Path.from_dict(pb[vertices[j].to_str()]).length / BASE_SPEED
            )
    return result


def expand(path: list[Coordinates]):
    with open(PRECALC_BASE_FILE, "r") as inp:
        pb = json.load(inp)
    result: list[Coordinates] = []
    prev_pos = path[0]
    for next_pos in path[1:]:
        if Coordinates(0, 0) in (prev_pos, next_pos):
            path = (
                Path.from_dict(pb[next_pos.to_str()]).path
                if next_pos != Coordinates(0, 0)
                else Path.from_dict(pb[prev_pos.to_str()]).path[::-1]
            )
            result.extend(path)
        else:
            result.extend([prev_pos, next_pos])
        prev_pos = next_pos
    return result


def make_distance_matrix(
    vertices: list[Coordinates], snow_areas: list[SnowArea], force_recalc=False
) -> Matrix:
    num_vertices = len(vertices)
    result: Matrix = [[0] * num_vertices for _ in range(num_vertices)]

    if force_recalc or not os.path.exists(TIMES_MATRIX_PATH):
        with tqdm(total=num_vertices * num_vertices // 2) as pbar:
            for i in range(num_vertices):
                for j in range(num_vertices):
                    if i > j:
                        dist, snow_dist, _ = segment_dist(
                            vertices[i], vertices[j], snow_areas
                        )
                        time = segment_time(dist, snow_dist)
                        result[i][j] = result[j][i] = time
                        pbar.update()
        with open(TIMES_MATRIX_PATH, "w") as out:
            json.dump(result, out)
    else:
        with open(TIMES_MATRIX_PATH, "r") as inp:
            result = json.load(inp)
    return result


def create_data_model(
    vertices: list[Coordinates],
    snow_areas: list[SnowArea],
    stack_of_bags: list[Bag],
    distance_matrix: Matrix | None,
) -> dict:
    """Stores the data for the problem."""
    data = {}
    matrix = (
        distance_matrix
        if distance_matrix
        else update_matrix(make_distance_matrix(vertices, snow_areas), vertices)
    )
    data["distance_matrix"] = [[round(e) for e in row] for row in matrix]
    data["demands"] = [0] + [1] * (len(vertices) - 1)
    data["vehicle_capacities"] = [len(bag) for bag in stack_of_bags[::-1]]
    data["num_vehicles"] = len(stack_of_bags)
    data["depot"] = 0
    return data


def print_solution(
    vertices: list[Coordinates], data, manager, routing, assignment
) -> list[Coordinates]:
    """Prints assignment on console."""
    moves = []
    print(f"Objective: {assignment.ObjectiveValue()}")
    # Display dropped nodes.
    dropped_nodes = "Dropped nodes:"
    for node in range(routing.Size()):
        if routing.IsStart(node) or routing.IsEnd(node):
            continue
        if assignment.Value(routing.NextVar(node)) == node:
            dropped_nodes += " {}".format(manager.IndexToNode(node))
    print(dropped_nodes)
    # Display routes
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data["demands"][node_index]
            moves.append(vertices[node_index])

            plan_output += " {0} Load({1}) -> ".format(node_index, route_load)
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        plan_output += " {0} Load({1})\n".format(manager.IndexToNode(index), route_load)
        moves.append(vertices[manager.IndexToNode(index)])

        plan_output += "Time of the route: {} s\n".format(route_distance)
        plan_output += "Load of the route: {}\n".format(route_load)
        # print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print("Total time of all routes: {} s".format(total_distance))
    print("Total Load of all routes: {}".format(total_load))
    return moves


def solve(
    map_data: Map,
    stack_of_bags: list[Bag],
    distance_matrix: Matrix | None = None,
    tl: int = 1,
):
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    vertices: list[Coordinates] = [Coordinates(0, 0)] + map_data.children
    data = create_data_model(
        vertices, map_data.snow_areas, stack_of_bags, distance_matrix
    )

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data["vehicle_capacities"],  # vehicle maximum capacities
        True,  # start cumul to zero
        "Capacity",
    )

    # Allow to drop nodes.
    # penalty = 1000
    # for node in range(1, len(data['distance_matrix'])):
    #     routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(tl)

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if assignment:
        return print_solution(vertices, data, manager, routing, assignment)


if __name__ == "__main__":
    sus_map = load_map()
    bags = load_bags()
    bags.sort(key=len, reverse=True)
    moves = solve(sus_map, bags, tl=int(input("Time limit: ")))
    if moves:
        solution = Route(moves=moves, stack_of_bags=bags, map_id=MAP_ID)
        solution.moves = cleanup_jumps_to_start(
            expand(cleanup_jumps_to_start(solution.moves))
        )
        save(solution, "./data/solution_vrp.json")
