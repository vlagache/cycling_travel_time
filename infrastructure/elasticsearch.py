import logging

import elasticsearch
from elasticsearch import exceptions

from utils.functions import transforms_string_in_datetime


class Elasticsearch:
    es_logger = logging.getLogger('elasticsearch')
    es_logger.setLevel(logging.WARNING)

    def __init__(self, local_connect=False):
        self.local_connect = local_connect
        if self.local_connect:
            hosts = [{"host": 'localhost', "port": 9200}]
        else:
            hosts = [{"host": 'elasticsearch', "port": 9200}]
        self.database = elasticsearch.Elasticsearch(hosts=hosts)

    def store_data(self, data_json, index_name, id_data=None):
        if id_data is not None:
            es_object = self.database.index(
                index=index_name,
                id=id_data,
                body=data_json
            )
        else:
            es_object = self.database.index(
                index=index_name,
                body=data_json
            )
        return es_object.get('_id')

    def check_if_doc_exists(self, index_name, id_data):
        return self.database.exists(
            index=index_name,
            id=id_data
        )

    def get_doc_by_id(self, index_name, id_data):
        result = self.database.search(
            index=index_name,
            body={"query": {"match": {"_id": id_data}}})

        if result['hits']['total']['value'] == 0:
            return None
        else:
            doc = result['hits']['hits'][0]['_source']
            return doc

    def retrieve_general_info_on_activities(self):
        """
        Returns a dictionary with :
        number of activities in base
        name of the last activity
        date of the last activity
        """

        try:
            query = {
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {"start_date_local": "desc"}
                ]
            }
            results = self.database.search(index="index_activity",
                                           body=query)

            activities_in_base = results['hits']['total']['value']
            name_last_activity = results['hits']['hits'][0]['_source']['name']
            date_last_activity = results['hits']['hits'][0]['_source']['start_date_local']
            format_date_last_activity = transforms_string_in_datetime(date_last_activity)
            info_activities = {
                'activities_in_base': activities_in_base,
                'name_last_activity': name_last_activity,
                'format_date_last_activity': format_date_last_activity
            }
            return info_activities

        except exceptions.NotFoundError:
            return None

    def retrieve_general_info_on_routes(self):
        try:
            query = {
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {"created_at": "desc"}
                ]
            }
            results = self.database.search(index="index_route",
                                           body=query)
            routes_in_base = results['hits']['total']['value']
            name_last_route = results['hits']['hits'][0]['_source']['name']
            date_last_route = results['hits']['hits'][0]['_source']['created_at']
            format_date_last_route = transforms_string_in_datetime(date_last_route)
            info_routes = {
                'routes_in_base': routes_in_base,
                'name_last_route': name_last_route,
                'format_date_last_route': format_date_last_route
            }
            return info_routes

        except exceptions.NotFoundError:
            return None

    def search_user(self, first_name, last_name):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "athlete.firstname": first_name
                            }
                        },
                        {
                            "match": {
                                "athlete.lastname": last_name
                            }
                        }
                    ]
                }
            }
        }
        response = self.database.search(index="index_user", body=query)

        if response['hits']['total']['value'] == 0:
            return None
        elif response['hits']['total']['value'] == 1:
            return response['hits']['hits'][0]

    def check_if_user_exist(self, first_name, last_name):

        try:
            response = self.search_user(first_name, last_name)

            if response is not None:
                return True
            else:
                return False
        # If the index does not yet exist
        except exceptions.NotFoundError:
            return False

    def update_tokens_user(self,
                           access_token,
                           refresh_token,
                           token_expires_at,
                           user_id):
        body = {
            "doc": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": token_expires_at
            }
        }

        self.database.update(index="index_user",
                             id=user_id,
                             body=body)
