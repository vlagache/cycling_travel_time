import logging
import os.path
import time

import requests
from dotenv import load_dotenv

from infrastructure.elasticsearch import Elasticsearch


class ImportStrava:
    load_dotenv()

    def __init__(self, access_token, refresh_token, token_expires_at, user_id, dao: Elasticsearch):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self.user_id = user_id
        self.dao = dao

    def check_if_token_is_valid(self):
        """
        Checks if the access_token is still valid
        Return True/False
        """
        if self.token_expires_at < time.time():
            logging.info("Token expired")
            return False
        else:
            logging.info("Token is still valid")
            return True

    def refresh_strava_token(self):
        """
        Send to strava the refresh_token to get a new access_token and a new refresh_token.
        """
        logging.info("Token refreshment")
        strava_request = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': os.getenv("STRAVA_CLIENT_ID"),
                'client_secret': os.getenv("STRAVA_CLIENT_SECRET"),
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
        )

        self.access_token = strava_request.json()['access_token']
        self.refresh_token = strava_request.json()['refresh_token']
        self.token_expires_at = strava_request.json()['expires_at']

        self.dao.update_tokens_user(access_token=self.access_token,
                                    refresh_token=self.refresh_token,
                                    token_expires_at=self.token_expires_at,
                                    user_id=self.user_id)

    def refresh_token_if_not_valid(self):
        """
        Refreshes access token if it is no longer valid.
        """
        if not self.check_if_token_is_valid():
            self.refresh_strava_token()

    def get_all_activities_ids(self):
        """
        Recovers all cycling strava activities ids
        Returns the list of the ids of the activities entered in base
        """

        self.refresh_token_if_not_valid()

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
        logging.info(f'Recovery of {len(activities_ids)} activities from Strava')

        return activities_ids

    def get_new_activities(self):
        """
        From the list of all Strava's activities, removing of ones
        that are already in the database so as not to request them again.
        Returns ids of the activities to be added
        """
        activities_ids = self.get_all_activities_ids()
        activities_ids_to_added = [
            activity_id for activity_id in activities_ids if not self.dao.check_if_doc_exists(
                index_name="index_activity",
                id_data=activity_id
            )
        ]
        logging.info(f'{len(activities_ids_to_added)} new activities to be added to the database')
        return activities_ids_to_added

    def get_activity_by_id(self, activity_id):
        """
        retrieve all the information of an activity on Strava
        """
        strava_request = requests.get(
            f'https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=',
            headers={
                'Authorization': f'Bearer {self.access_token}'
            }
        )
        activity_json = strava_request.json()

        return activity_json

    def storage_of_new_activities(self):
        """
        Stores on the database all new activities
        """
        activities_ids_to_added = self.get_new_activities()
        for activity_id in activities_ids_to_added:
            activity_json = self.get_activity_by_id(activity_id=activity_id)
            self.dao.store_data(
                data_json=activity_json,
                index_name='index_activity',
                id_data=activity_json['id']
            )
        logging.info(f'{len(activities_ids_to_added)} activities added to the database')
