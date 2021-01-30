import json
import logging

import elasticsearch
import jsonpickle
from elasticsearch import exceptions

from prediction.domain.activity import Activity, ActivityRepository
from prediction.domain.athlete import Athlete, AthleteRepository
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

    def update_data(self, index_name, id_data, body):
        self.database.update(index=index_name,
                             id=id_data,
                             body=body)

    def check_if_doc_exists(self, index_name, id_data):
        return self.database.exists(
            index=index_name,
            id=id_data
        )

    def search_with_query(self, index_name, query: dict):
        return self.database.search(index=index_name, body=query)

    def search_by_id(self, index_name, id_data):
        return self.database.search(
            index=index_name,
            body={"query": {"match": {"_id": id_data}}})

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


class ElasticActivityRepository(ActivityRepository):
    #TODO : DEBUG to remove
    index = "index_activity_test"

    def __init__(self):
        self.elastic = Elasticsearch(local_connect=True)
        self.elastic.add_index(self.index)

    def get(self, id_) -> Activity:
        result = self.elastic.search_by_id(index_name=self.index,
                                           id_data=id_)
        activity = jsonpickle.decode(read(result['hits']['hits'][0]['_source']))
        return activity

    def save(self, activity: Activity):
        return self.elastic.store_data(
            data=jsonpickle.encode(activity),
            index_name=self.index,
            id_data=activity.id
        )

    def search_if_exist(self, _id) -> bool:
        return self.elastic.check_if_doc_exists(
            index_name=self.index,
            id_data=_id
        )


class ElasticAthleteRepository(AthleteRepository):
    index = "index_athlete"

    def __init__(self):
        self.elastic = Elasticsearch(local_connect=True)
        self.elastic.add_index(self.index)

    def get(self, id_) -> Athlete:
        result = self.elastic.search_by_id(index_name=self.index,
                                           id_data=id_)
        athlete = jsonpickle.decode(read(result['hits']['hits'][0]['_source']))
        return athlete

    def save(self, athlete: Athlete):
        return self.elastic.store_data(
            data=jsonpickle.encode(athlete),
            index_name=self.index,
            id_data=athlete.id
        )

    def update_tokens(self, id_, access_token, refresh_token, token_expires_at):
        body = {
            "doc": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": token_expires_at
            }
        }
        self.elastic.update_data(
            index_name=self.index,
            id_data=id_,
            body=body
        )

    def search_if_exist(self, firstname, lastname) -> Athlete:
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
        result = self.elastic.search_with_query(index_name=self.index, query=query)
        if result['hits']['total']['value'] == 1:
            athlete = jsonpickle.decode(read(result['hits']['hits'][0]['_source']))
            return athlete
