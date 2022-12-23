from util import get_map, send_solution, get_solution_info, save_map, load_map
from data import Route
from constants import MAP_ID, MAP_FILE_PATH
import os

if __name__ == '__main__':
    if not os.path.exists(MAP_FILE_PATH):
        sus_map = get_map()
        save_map(sus_map)
    else:
        sus_map = load_map()
    sus_solution = Route(moves=[sus_map.children[0]], map_id=MAP_ID,
                         stack_of_bags=[[sus_map.gifts[0].id]])
    print('=== SOLUTION ===')
    print(sus_solution)
    sus_response = send_solution(sus_solution)
    print('=== RESPONSE ===')
    print(sus_response)
    print('=== INFO ===')
    if sus_response.success:
        print(get_solution_info(sus_response.round_id))
    else:
        print('Unsuccessful')
