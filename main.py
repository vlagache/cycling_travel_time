import logging
import webbrowser

from infrastructure.import_strava import ImportStrava

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S',
                        level=logging.DEBUG)

    # if the user has already given access to his account a token is available

    # TODO: we check if the user has a token and if it is still valid,
    #  for the moment we use a Json file but it will be in a database.

    import_strava = ImportStrava()
    if import_strava.check_token_exists():
        if not import_strava.check_token_is_valid():
            # TODO:once the new token is retrieved the process
            #  should be restarted automatically
            import_strava.refresh_strava_token()

        # import_strava.get_all_activities_ids()
        import_strava.get_segments_for_activity(id_activity=None)

    else:
        webbrowser.open('http://localhost:8090/strava_authorize')