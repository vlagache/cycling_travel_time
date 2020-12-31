import json
import logging
import os.path
import time

import requests
from dotenv import load_dotenv


class ImportStrava:
    load_dotenv()

    def __init__(self, dao):
        self.access_token = None
        self.refresh_token = None
        self.dao = dao

    @staticmethod
    def check_token_exists():
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
        self.access_token = strava_request.json()['access_token']
        with open('strava_token.json', 'w') as outfile:
            json.dump(strava_request.json(), outfile)

    def get_all_activities_ids(self):
        """
        Recovers all cycling strava activities ids
        Returns the list of the ids of the activities entered in base
        """
        mandatory_type_activity = ['VirtualRide', 'Ride']
        page_number = 1
        activities_ids = []
        while True:
            strava_request = requests.get(
                'https://www.strava.com/api/v3/athlete/activities',
                params={
                    'per_page': 200,
                    'page': page_number
                },
                headers={
                    'Authorization': f'Bearer {self.access_token}'
                }
            )
            if not strava_request.json():
                break

            for activity in strava_request.json():
                if activity['type'] not in mandatory_type_activity:
                    continue
                activities_ids.append(activity['id'])
            page_number += 1
        logging.info(f'Recovery of {len(activities_ids)} activities')

        return activities_ids

    def store_activity(self, activity_id):
        strava_request = requests.get(
            f'https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=',
            headers={
                'Authorization': f'Bearer {self.access_token}'
            }
        )
        activity_json = strava_request.json()
        self.dao.store_data(
            data_json=activity_json,
            index_name='index_activity',
            id_data=activity_json['id']
        )
