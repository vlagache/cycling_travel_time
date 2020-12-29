import json
import logging
import os.path
import time
from pprint import pprint

import requests
from dotenv import load_dotenv


class ImportStrava:
    load_dotenv()

    def __init__(self):
        self.access_token = None
        self.refresh_token = None

    def check_token_exists(self):
        if os.path.exists('strava_token.json'):
            return True
        else:
            return False

    def check_token_is_valid(self):
        with open('strava_token.json') as json_file:
            strava_tokens = json.load(json_file)

        if strava_tokens['expires_at'] < time.time():
            logging.info("Token expired")
            self.refresh_token = strava_tokens['refresh_token']
            return False
        else:
            logging.info("Token still valid")
            self.access_token = strava_tokens['access_token']
            return True

    def refresh_strava_token(self):
        strava_request = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': os.getenv("STRAVA_CLIENT_ID"),
                'client_secret': os.getenv("STRAVA_CLIENT_SECRET"),
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        print(strava_request.json())
        with open('strava_token.json', 'w') as outfile:
            json.dump(strava_request.json(), outfile)

    def get_all_activities(self):
        ids_list = []
        mandatory_type_activity = ['VirtualRide', 'Ride']
        page_number = 1
        while True:
            if page_number > 1:
                break
            strava_request = requests.get(
                'https://www.strava.com/api/v3/athlete/activities',
                params={
                    'per_page': 1,
                    'page': page_number
                },
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                }
            )
            if not strava_request.json():
                break

            pprint(strava_request.json())
            print(len(strava_request.json()))
            for activity in strava_request.json():
                # TODO : activity in database
                if activity['type'] not in mandatory_type_activity:
                    continue
                print(activity['name'])
                print(activity['type'])
                print(activity['id'])
                print(activity['start_date'])
            page_number += 1

    def get_segments_for_activity(self, id_activity):
        id_activity = '4513379684'
        strava_request = requests.get(
            f'https://www.strava.com/api/v3/activities/{id_activity}?include_all_efforts=',
            headers={
                'Authorization': f'Bearer {self.access_token}'
            }
        )
        pprint(strava_request.json())
