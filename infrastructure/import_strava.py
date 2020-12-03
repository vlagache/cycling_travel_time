import gzip
import os
import shutil

import fitparse
import pandas as pd


class ImportStrava:
    directory_files = 'import_strava/activities/'
    directory_csv = 'import_strava/activities.csv'
    directory_files_dezip = 'import_strava/activities_dezip/'

    def __init__(self):
        self.cycling_fit_files_names = None
        self.files_missing_infos = []

    def get_cycling_activities_fit_file(self):
        """
        Getting the .csv summary of Strava's "Vélo" activities
        Keeps only .fit files
        File names are kept in the form 15122.fit.gz
        """
        df = pd.read_csv(self.directory_csv)
        activities_type = df["Type d'activité"].unique()

        # We only take "Vélo" activities
        cycling_activity_type = [
            activity_type for activity_type in activities_type if 'Vélo' in activity_type
        ]
        df_cycling = df.loc[df["Type d'activité"].isin(cycling_activity_type)]
        cycling_fit_files_names = df_cycling['Nom du fichier'].values

        # Some files are in .gpx, we remove them from the list.
        cycling_fit_files_names = [
            fit_file_name for fit_file_name in cycling_fit_files_names if ".gpx" not in fit_file_name
        ]

        # remove "activities" from the name of each of the files
        cycling_fit_files_names = [
            fit_file_name.replace('activities/', '') for fit_file_name in cycling_fit_files_names
        ]

        self.cycling_fit_files_names = cycling_fit_files_names

    def dezip_file(self):
        """
        dezip all .fit files and rename as 15122.fit
        """
        i = 1
        for cycling_fit_file_name in self.cycling_fit_files_names:
            print(cycling_fit_file_name)
            with gzip.open(self.directory_files + cycling_fit_file_name, 'r') as f_in, open(
                    self.directory_files_dezip + cycling_fit_file_name.replace('.gz', ''), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            i += 1
        print(f'{i} files have been unzipped')

    def test_fit_file(self):

        """
        Not all files have the same information.
        We want at least the following information : timestamp , distance , altitude
        If there is not enough information we delete the files.
        """

        mandatory_informations = ['altitude', 'distance', 'timestamp']
        fit_files_dezip = os.listdir(self.directory_files_dezip)

        files_with_missing_infos = 0
        files_missing_infos = []

        for fit_file_dezip in fit_files_dezip:
            fit_file_path = self.directory_files_dezip + fit_file_dezip
            fit_parse = fitparse.FitFile(fit_file_path)

            i = 0
            current_informations = []
            for record in fit_parse.get_messages("record"):
                if i > 0:
                    break
                for data in record:
                    current_informations.append(data.name)
                i += 1

            check = all(info in current_informations for info in mandatory_informations)
            if check:
                print(f'{fit_file_dezip} : OK ')
            else:
                print(f'{fit_file_dezip} : Missing Infos ')
                files_with_missing_infos += 1
                self.files_missing_infos.append(fit_file_dezip)

        # CHERCHER POURQUOI !