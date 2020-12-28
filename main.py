import logging
import os

from domain.road import Road
from infrastructure.import_strava import ImportStrava

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S',
                        level=logging.DEBUG)
    # logging.debug('This message should go to the log file')
    # logging.info('So should this')
    # logging.warning('And this, too')
    # logging.error('And non-ASCII stuff, too, like Øresund and Malmö')

    import_strava = ImportStrava()
    # import_strava.get_cycling_activities_fit_file()
    # import_strava.unzip_file()
    # import_strava.delete_files_missing_info()

    fit_files_unzip = os.listdir(import_strava.directory_files_unzip)

    i = 0
    activity_number = 1
    segments = 0
    logging.info("Segmentation des fichiers .fit")
    for fit_file_unzip in fit_files_unzip:
        if i > 1:
            break
        file_path = import_strava.directory_files_unzip + fit_file_unzip

        road = Road(file_path)
        road.parsing_from_fit_file()
        road.compute_segmentation()
        road.compute_metrics_segments(activity_number)
        road.compute_type_previous_segment()
        road.debug_strava()
        i += 1
        activity_number += 1
        segments += len(road.segments)

    logging.info(f"{activity_number - 1} fichier(s) segmentés en {segments} segments")

    # road = Road(fit_file="./fit_files/alpes.fit")

### pour chaque segment d'une route
### Injection en base de données
