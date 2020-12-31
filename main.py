import logging
import webbrowser

from infrastructure.elasticsearch import Elasticsearch
from infrastructure.import_strava import ImportStrava

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S',
                        level=logging.DEBUG)

    # if the user has already given access to his account a token is available

    # TODO: we check if the user has a token and if it is still valid,
    #  for the moment we use a Json file but it will be in a database.

    elasticsearch = Elasticsearch(local_connect=True)
    import_strava = ImportStrava(elasticsearch)

    if import_strava.check_token_exists():
        if not import_strava.check_token_is_valid():
            # replace the old token by the new one
            import_strava.refresh_strava_token()

        activities_ids = import_strava.get_all_activities_ids()
        existing_activities = 0
        added_activities = 0
        for activity_id in activities_ids:
            if elasticsearch.check_if_doc_exists(
                    index_name='index_activity',
                    id_data=activity_id
            ):
                existing_activities += 1
                continue
            else:
                import_strava.store_activity(activity_id=activity_id)
                added_activities += 1

        logging.info(f'{added_activities} added in Elasticsearch , {existing_activities} already present in database')
    else:
        # TODO : After the user's authorization, how can
        #  we proceed with the rest of the process?
        webbrowser.open('http://localhost:8090/strava_authorize')
