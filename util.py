from constants import SUBMISSION_URL, AUTH_HEADER
from data import Route, RouteResponse
from requests import post


def send_solution(solution: Route) -> RouteResponse:
    response = post(SUBMISSION_URL, json=solution.to_json(), headers=AUTH_HEADER)
    return RouteResponse.from_json(response.text)
