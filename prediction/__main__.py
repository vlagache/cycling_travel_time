import argparse
import logging
import sys
import time

import uvicorn
from dotenv import load_dotenv

from prediction.domain import athlete, activity, route, model
from prediction.infrastructure.elasticsearch import \
    ElasticAthleteRepository, ElasticActivityRepository, ElasticRouteRepository, ElasticModelRepository
from prediction.infrastructure.elasticsearch import Elasticsearch
from prediction.infrastructure.webservice import app

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S',
                        stream=sys.stdout,
                        level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--local_connect",
                        help="use local connection of elastic",
                        action="store_true")

    args = parser.parse_args()

    if args.local_connect:
        load_dotenv()

    # To wait for Elasticsearch to be fully started...
    while not Elasticsearch(local_connect=args.local_connect).ping():
        logging.info("Waiting for ElasticSearch to start up completely")
        time.sleep(2)

    athlete.repository = ElasticAthleteRepository(args.local_connect)
    activity.repository = ElasticActivityRepository(args.local_connect)
    route.repository = ElasticRouteRepository(args.local_connect)
    model.repository = ElasticModelRepository(args.local_connect)

    uvicorn.run(app, port=8090, host='0.0.0.0', log_level='debug')
