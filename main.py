import logging
from infrastructure.import_strava import ImportStrava

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S',
                        level=logging.INFO)
    # logging.debug('This message should go to the log file')
    # logging.info('So should this')
    # logging.warning('And this, too')
    # logging.error('And non-ASCII stuff, too, like Øresund and Malmö')


    import_strava = ImportStrava()
    # import_strava.get_cycling_activities_fit_file()
    # import_strava.unzip_file()
    # import_strava.delete_files_missing_info()
    # import_strava.move_files_missing_info()
    import_strava.delete_file_wrong_timedelta(desired_average_timedelta=1)



    # road = Road(fit_file="./fit_files/alpes.fit")
    # road.parsing_from_fit_file()
    # road.compute_segmentation()
    # road.compute_metrics_segments()
    # road.compute_type_previous_segment()
    # road.debug_strava()

### pour chaque segment d'une route
### Injection en base de données
