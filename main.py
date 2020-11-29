from domain.road import Road
from domain.segment import Segment

if __name__ == "__main__":

    ### Connection a l'api Strava
    ### Recuperation de tout les fichiers .fit
    ### Pour chaque fichier .fit logique suivante =>

    road = Road(fit_file="./fit_files/alpes.fit")
    road.parsing_from_fit_file()
    road.compute_segmentation()
    road.compute_metrics_segments()
    road.compute_type_previous_segment()
    road.debug_strava()

   ### pour chaque segment d'une route
   ### Injection en base de données