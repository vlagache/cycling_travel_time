import json
import logging

import elasticsearch
import jsonpickle
from elasticsearch import exceptions

from domain.athlete import Athlete, AthleteRepository
from utils.functions import transforms_string_in_datetime


def read(obj):
    if isinstance(obj, dict):
        return json.dumps(obj)
    return obj


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

    def add_index(self, index: str):
        try:
            self.database.indices.create(index=index)
        except elasticsearch.exceptions.RequestError:
            pass

    def store_data(self, data, index_name, id_data=None):
        if id_data is not None:
            es_object = self.database.index(
                index=index_name,
                id=id_data,
                body=data
            )
        else:
            es_object = self.database.index(
                index=index_name,
                body=data
            )
        return es_object.get('_id')

    def check_if_doc_exists(self, index_name, id_data):
        return self.database.exists(
            index=index_name,
            id=id_data
        )

    def check_match_with_query(self, index_name, query: dict):
        response = self.database.search(index=index_name, body=query)
        if response['hits']['total']['value'] == 1:
            return response['hits']['hits'][0]

    def get_doc_by_id(self, index_name, id_data):
        result = self.database.search(
            index=index_name,
            body={"query": {"match": {"_id": id_data}}})

        if result['hits']['total']['value'] == 0:
            return None
        else:
            doc = result['hits']['hits'][0]['_source']
            return doc

        #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####

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


class ElasticAthleteRepository(AthleteRepository):
    index = "index-athlete"

    def __init__(self):
        self.elastic = Elasticsearch(local_connect=True)
        self.elastic.add_index(self.index)

    def save(self, athlete: Athlete):
        return self.elastic.store_data(
            data=jsonpickle.encode(athlete),
            index_name=self.index,
            id_data=athlete.id
        )

    def check_if_exist(self, firstname, lastname) -> Athlete:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "firstname": firstname
                            }
                        },
                        {
                            "match": {
                                "lastname": lastname
                            }
                        }
                    ]
                }
            }
        }
        result = self.elastic.check_match_with_query(index_name=self.index, query=query)
        if result is not None:
            athlete = jsonpickle.decode(read(result.get("_source")))
            return athlete
