import random
import math


def simulated_annealing(initial_state, get_cost, get_neighbor):
    """Peforms simulated annealing to find a solution"""
    initial_temp = 90
    final_temp = 0.1
    alpha = 10

    current_temp = initial_temp

    # Start by initializing the current state with the initial state
    current_state = initial_state
    solution = current_state

    while current_temp > final_temp:
        neighbor = get_neighbor(current_state)

        # Check if neighbor is best so far
        cost_diff = get_cost(current_state) - get_cost(neighbor)

        # if the new solution is better, accept it
        if cost_diff > 0:
            solution = neighbor
            current_state = neighbor
        # if the new solution is not better, accept it with a probability of e^(-cost/temp)
        else:
            if random.uniform(0, 1) < math.exp(-cost_diff / current_temp):
                current_state = neighbor
        # decrement the temperature
        current_temp -= alpha

    return solution
