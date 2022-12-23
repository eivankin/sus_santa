from dotenv import load_dotenv

import os

load_dotenv()
API_KEY = os.getenv('API_KEY')
MAP_ID = os.getenv('MAP_ID')

BASE_URL = 'https://datsanta.dats.team'
SUBMISSION_URL = BASE_URL + '/api/round'
AUTH_HEADER = {'X-API-Key': API_KEY}
