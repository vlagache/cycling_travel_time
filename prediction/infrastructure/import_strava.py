import logging
import os.path
import time

import requests
from dotenv import load_dotenv

from prediction.domain import athlete, activity
from prediction.infrastructure import adapter_data


class ImportStrava:
    load_dotenv()

    # def __init__(self, access_token, refresh_token, token_expires_at, user_id, dao: Elasticsearch):
    #     self.access_token = access_token
    #     self.refresh_token = refresh_token
    #     self.token_expires_at = token_expires_at
    #     self.user_id = user_id
    #     self.dao = dao

    def __init__(self, athlete_: athlete.Athlete):
        self.athlete = athlete_

    def check_if_token_is_valid(self):
        """
        Checks if the access_token is still valid
        Return True/False
        """
        if self.athlete.token_expires_at < time.time():
            logging.info("Token expired")
            return False
        else:
            logging.info("Token is still valid")
            return True

    def refresh_token_if_not_valid(self):
        """
        Refreshes access token if it is no longer valid.
        """
        if not self.check_if_token_is_valid():
            self.refresh_token()

    def refresh_token(self):
        """
        Send to strava the refresh_token to get a new access_token and a new refresh_token.
        """
        logging.info("Token refreshment")
        strava_request = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': os.getenv("STRAVA_CLIENT_ID"),
                'client_secret': os.getenv("STRAVA_CLIENT_SECRET"),
                'refresh_token': self.athlete.refresh_token,
                'grant_type': 'refresh_token'
            }
        )

        self.athlete.access_token = strava_request.json()['access_token']
        self.athlete.refresh_token = strava_request.json()['refresh_token']
        self.athlete.token_expires_at = strava_request.json()['expires_at']

        athlete.repository.update_tokens(id_=self.athlete.id,
                                         access_token=self.athlete.access_token,
                                         refresh_token=self.athlete.refresh_token,
                                         token_expires_at=self.athlete.token_expires_at)

    # ACTIVITIES

    def get_all_activities_ids(self):
        """
        Recovers all cycling strava activities ids
        Returns the list of the ids of the activities
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
                    'Authorization': f'Bearer {self.athlete.access_token}'
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

    def get_activity_by_id(self, activity_id):
        """
        retrieve all the information of an activity on Strava
        """
        strava_request = requests.get(
            f'https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=',
            headers={
                'Authorization': f'Bearer {self.athlete.access_token}'
            }
        )
        activity_json = strava_request.json()

        return activity_json

    def get_new_activities_ids(self):
        """
        From the list of all Strava's activities, removing of ones
        that are already in the database so as not to request them again.
        Returns ids of the activities to be added
        """
        activities_ids = self.get_all_activities_ids()
        activities_ids_to_added = [
            activity_id for activity_id in activities_ids
            if not activity.repository.search_if_exist(_id=activity_id)
        ]
        logging.info(f'{len(activities_ids_to_added)} new activities to be added to the database')
        return activities_ids_to_added

    def storage_of_new_activities(self):
        """
        Stores on the database all new activities
        """
        activities_ids_to_added = self.get_new_activities_ids()
        activities_added = 0
        if len(activities_ids_to_added) != 0:
            for activity_id in activities_ids_to_added:
                # TODO : DEBUG to remove
                if activities_added == 1:
                    break
                activity_json = self.get_activity_by_id(activity_id=activity_id)
                activity_ = adapter_data.AdapterActivity(activity_json).get()
                activity.repository.save(activity_)
                # elastic.store_data(
                #     data=activity_json,
                #     index_name='index_activity',
                #     id_data=activity_json['id']
                # )
                activities_added += 1
            logging.info(f'{activities_added} activities added to the database')
        return activities_added

    # ROUTES

    def store_all_routes_athlete(self):
        """
        Stores all the athlete's routes on Elasticsearch together with the gpx file
        """
        self.refresh_token_if_not_valid()
        page_number = 1
        routes_number = 0
        while True:
            strava_request = requests.get(
                f'https://www.strava.com/api/v3/athletes/{self.athlete.id}/routes',
                params={
                    'per_page': 200,
                    'page': page_number
                },
                headers={
                    'Authorization': f'Bearer {self.athlete.access_token}'
                }
            )
            if not strava_request.json():
                break

            for route in strava_request.json():
                gpx_file = self.get_route_gpx(route['id'])
                route['gpx_file'] = gpx_file
                self.dao.store_data(
                    data_json=route,
                    index_name='index_route',
                    id_data=route['id']
                )
                routes_number += 1
            page_number += 1

        logging.info(f'{routes_number} routes added to the database')

    def get_route_gpx(self, route_id):
        """
        Retrieve a gpx file of a route from its id
        """
        strava_request = requests.get(
            f'https://www.strava.com/api/v3/routes/{route_id}/export_gpx',
            headers={
                'Authorization': f'Bearer {self.athlete.access_token}'
            }
        )
        gpx_file = strava_request.text
        return gpx_file
