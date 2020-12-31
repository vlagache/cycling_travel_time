import logging

import elasticsearch


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

    def check_doc_exists(self, index_name, id_data):
        return self.database.exists(
            index=index_name,
            id=id_data
        )
