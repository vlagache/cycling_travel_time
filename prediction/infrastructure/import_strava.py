import logging
import os.path
import time
from typing import List, Dict

import requests
from dotenv import load_dotenv

from prediction.domain import athlete, activity, route
from prediction.infrastructure import adapter_data
from utils.functions import gpx_parser, compute_segmentation


class ImportStrava:
    load_dotenv()

    def __init__(self, athlete_: athlete.Athlete):
        self.athlete = athlete_
        self.refresh_token_if_not_valid()

    def check_if_token_is_valid(self) -> bool:
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

    def refresh_token_if_not_valid(self) -> None:
        """
        Refreshes access token if it is no longer valid.
        """
        if not self.check_if_token_is_valid():
            self.refresh_token()

    def refresh_token(self) -> None:
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

        athlete.repository.save(self.athlete)

    # ACTIVITIES

    def get_all_activities_ids(self) -> List:
        """
        Recovers all cycling strava activities ids
        Returns the list of the ids of the activities
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
                    'Authorization': f'Bearer {self.athlete.access_token}'
                }
            )
            if not strava_request.json():
                break

            for activity_json in strava_request.json():
                if activity_json['type'] in mandatory_type_activity:
                    activities_ids.append(activity_json['id'])

            page_number += 1
        logging.info(f'Recovery of {len(activities_ids)} activities from Strava')

        return activities_ids

    def get_activity_by_id(self, activity_id: int) -> Dict:
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

    def get_new_activities_ids(self) -> List:
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

    def storage_of_new_activities(self) -> int:
        """
        Stores on the database all new activities
        Return number of activities added for frontend
        """
        activities_ids_to_added = self.get_new_activities_ids()
        activities_added = 0
        if len(activities_ids_to_added) != 0:
            for activity_id in activities_ids_to_added:
                activity_json = self.get_activity_by_id(activity_id=activity_id)
                activity_ = adapter_data.AdapterActivity(activity_json).get()
                activity.repository.save(activity_)
                activities_added += 1
            logging.info(f'{activities_added} activities added to the database')
        return activities_added

    # ROUTES

    def get_all_routes_ids(self) -> List:
        """
          Recovers all strava routes ids
          Returns the list of the ids of routes
        """
        page_number = 1
        routes_ids = []
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

            for route_json in strava_request.json():
                routes_ids.append(route_json['id'])

            page_number += 1

        logging.info(f'Recovery of {len(routes_ids)} routes from Strava')
        return routes_ids

    def get_route_by_id(self, route_id: int) -> Dict:
        """
        retrieve all the information of a route on Strava
        """

        strava_request = requests.get(
            f'https://www.strava.com/api/v3/routes/{route_id}',
            headers={
                'Authorization': f'Bearer {self.athlete.access_token}'
            }
        )
        activity_json = strava_request.json()

        return activity_json

    def get_new_routes_ids(self) -> List:
        """
        From the list of all Strava's routes, removing of ones
        that are already in the database so as not to request them again.
        Returns ids of routes to be added
        """
        routes_ids = self.get_all_routes_ids()
        routes_ids_to_added = [
            route_id for route_id in routes_ids
            if not route.repository.search_if_exist(_id=route_id)
        ]
        logging.info(f'{len(routes_ids_to_added)} new routes to be added to the database')
        return routes_ids_to_added

    def storage_of_new_routes(self) -> int:
        """
        Stores on the database all new routes
        Return number of routes added for frontend
        """
        routes_ids_to_added = self.get_new_routes_ids()
        routes_added = 0
        if len(routes_ids_to_added) != 0:
            for route_id in routes_ids_to_added:
                route_json = self.get_route_by_id(route_id=route_id)
                gpx = self.get_route_gpx(route_id=route_id)
                parsed_gpx = gpx_parser(gpx)
                route_json['gpx'] = parsed_gpx
                route_json['segmentation'] = compute_segmentation(parsed_gpx)
                route_ = adapter_data.AdapterRoute(route_json).get()
                route.repository.save(route_)
                routes_added += 1
            logging.info(f'{routes_added} routes added to the database')
        return routes_added

    def get_route_gpx(self, route_id) -> str:
        """
        Retrieve a gpx file of a route from its id
        """
        strava_request = requests.get(
            f'https://www.strava.com/api/v3/routes/{route_id}/export_gpx',
            headers={
                'Authorization': f'Bearer {self.athlete.access_token}'
            }
        )
        gpx = strava_request.text
        return gpx
