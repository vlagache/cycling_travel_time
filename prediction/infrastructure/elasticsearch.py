import json
import logging
from typing import List, Optional, Dict

import elasticsearch
import jsonpickle

from prediction.domain.activity import Activity, ActivityRepository
from prediction.domain.athlete import Athlete, AthleteRepository
from prediction.domain.model import Model, ModelRepository
from prediction.domain.route import Route, RouteRepository
from prediction.utils.functions import transforms_string_in_datetime


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

    def get_index_docs_count(self, index_name):
        self.database.indices.refresh(index_name)
        return self.database.cat.count(index_name, params={"format": "json"})

    def search_with_query(self, index_name, query: dict):
        return self.database.search(
            index=index_name,
            size=2000,
            body=query)

    def search_index(self, index_name):
        return self.database.search(
            index=index_name,
            size=2000,
            body={"query": {"match_all": {}}}
        )

    def search_by_id(self, index_name, id_data):
        return self.database.get(index=index_name, id=id_data)

    def delete_recreates_index(self, index_name):
        self.database.indices.delete(index=index_name)
        self.add_index(index=index_name)

    def ping(self):
        return self.database.ping()


class ElasticActivityRepository(ActivityRepository):
    index = "index_activity"

    def __init__(self, local_connect: bool):
        self.elastic = Elasticsearch(local_connect=local_connect)
        self.elastic.add_index(self.index)

    def is_empty(self) -> bool:
        result = self.elastic.get_index_docs_count(self.index)
        if result[0].get("count") == "0":
            return True
        else:
            return False

    def get(self, id_) -> Activity:
        result = self.elastic.search_by_id(index_name=self.index,
                                           id_data=id_)
        activity = jsonpickle.decode(read(result.get("_source")))
        return activity

    def get_all_desc(self) -> List[Activity]:
        query = {
            "query": {
                "match_all": {}
            },
            "sort": [
                {"start_date_local": "desc"}
            ]
        }
        results = self.elastic.search_with_query(
            index_name=self.index,
            query=query
        )
        activities = [
            jsonpickle.decode((read(hit.get("_source"))))
            for hit in results.get("hits").get("hits")]
        return activities

    def get_general_info(self) -> Dict:
        if not self.is_empty():
            activities = self.get_all_desc()
            last_activity = activities[0]
            activities_in_base = len(activities)
            name_last_activity = last_activity.name
            date_last_activity = transforms_string_in_datetime(
                last_activity.start_date_local)
        else:
            activities_in_base = None
            name_last_activity = None
            date_last_activity = None

        return {
            'activities_in_base': activities_in_base,
            'name_last_activity': name_last_activity,
            'date_last_activity': date_last_activity,
        }

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

    def delete_recreates_index(self) -> None:
        return self.elastic.delete_recreates_index(self.index)


class ElasticAthleteRepository(AthleteRepository):
    index = "index_athlete"

    def __init__(self, local_connect=True):
        self.elastic = Elasticsearch(local_connect=local_connect)
        self.elastic.add_index(self.index)

    def get(self, id_) -> Athlete:
        result = self.elastic.search_by_id(index_name=self.index,
                                           id_data=id_)
        athlete = jsonpickle.decode(read(result.get("_source")))
        return athlete

    def get_all(self):
        return self.elastic.search_index(index_name=self.index)

    def save(self, athlete: Athlete):
        return self.elastic.store_data(
            data=jsonpickle.encode(athlete),
            index_name=self.index,
            id_data=athlete.id
        )

    def search_if_exist(self, firstname, lastname) -> Optional[Athlete]:
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

    def delete_recreates_index(self) -> None:
        return self.elastic.delete_recreates_index(self.index)


class ElasticRouteRepository(RouteRepository):
    index = "index_route"

    def __init__(self, local_connect: bool):
        self.elastic = Elasticsearch(local_connect=local_connect)
        self.elastic.add_index(self.index)

    def is_empty(self) -> bool:
        result = self.elastic.get_index_docs_count(self.index)
        if result[0].get("count") == "0":
            return True
        else:
            return False

    def get(self, id_) -> Route:
        result = self.elastic.search_by_id(index_name=self.index,
                                           id_data=id_)
        route = jsonpickle.decode(read(result.get("_source")))
        return route

    def get_all_desc(self) -> List[Route]:
        if not self.is_empty():
            query = {
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {"created_at": "desc"}
                ]
            }
            results = self.elastic.search_with_query(
                index_name=self.index,
                query=query
            )
            routes = [
                jsonpickle.decode((read(hit.get("_source"))))
                for hit in results.get("hits").get("hits")]
            return routes

    def get_general_info(self) -> Dict:
        if not self.is_empty():
            routes = self.get_all_desc()

            last_route = routes[0]
            routes_in_base = len(routes)
            name_last_route = last_route.name
            date_last_route = transforms_string_in_datetime(last_route.created_at)
        else:
            routes_in_base = None
            name_last_route = None
            date_last_route = None

        return {
            'routes_in_base': routes_in_base,
            'name_last_route': name_last_route,
            'date_last_route': date_last_route
        }

    def save(self, route: Route):
        return self.elastic.store_data(
            data=jsonpickle.encode(route),
            index_name=self.index,
            id_data=route.id
        )

    def search_if_exist(self, _id) -> bool:
        return self.elastic.check_if_doc_exists(
            index_name=self.index,
            id_data=_id
        )

    def delete_recreates_index(self) -> None:
        return self.elastic.delete_recreates_index(self.index)


class ElasticModelRepository(ModelRepository):
    index = "index_model"

    def __init__(self, local_connect: bool):
        self.elastic = Elasticsearch(local_connect=local_connect)
        self.elastic.add_index(self.index)

    def is_empty(self) -> bool:
        result = self.elastic.get_index_docs_count(self.index)
        if result[0].get("count") == "0":
            return True
        else:
            return False

    def get(self, id_) -> Model:
        result = self.elastic.search_by_id(index_name=self.index,
                                           id_data=id_)
        model = jsonpickle.decode(read(result.get("_source")))
        return model

    def get_all(self) -> List[Model]:
        query = {
            "query": {
                "match_all": {}
            }
        }
        results = self.elastic.search_with_query(
            index_name=self.index,
            query=query
        )
        activities = [
            jsonpickle.decode((read(hit.get("_source"))))
            for hit in results.get("hits").get("hits")]
        return activities

    def get_general_info(self) -> Optional[dict]:
        if not self.is_empty():
            models = self.get_all()
            for model_ in models:
                model_.training_date = transforms_string_in_datetime(model_.training_date)

            models = sorted(models, key=lambda model_: model_.training_date, reverse=True)
            last_model_trained = models[0]

            models_in_base = len(models)
            date_last_model = last_model_trained.training_date


        else:
            models_in_base = None
            date_last_model = None

        return {
            'models_in_base': models_in_base,
            'date_last_model': date_last_model
        }

    def get_better_mape(self) -> Model:
        """
        returns the model with the best MAPE (the weakest one).
        MAPE : Mean Absolut Percentage Error
        """
        query = {
            "query": {
                "match_all": {}
            },
            "sort": [
                {"mape": "asc"}
            ]
        }
        results = self.elastic.search_with_query(
            index_name=self.index,
            query=query
        )
        models = [
            jsonpickle.decode((read(hit.get("_source"))))
            for hit in results.get("hits").get("hits")]
        return models[0]

    def save(self, model: Model):
        return self.elastic.store_data(
            data=jsonpickle.encode(model),
            index_name=self.index,
            id_data=model.id
        )

    def delete_recreates_index(self) -> None:
        return self.elastic.delete_recreates_index(self.index)
