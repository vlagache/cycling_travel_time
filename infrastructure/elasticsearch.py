import logging

import elasticsearch
from elasticsearch import exceptions


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
