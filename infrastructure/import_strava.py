import datetime
import gzip
import logging
import os
import shutil

import fitparse
import pandas as pd


class ImportStrava:
    directory_files = 'import_strava/activities/'
    activities_full_csv = 'import_strava/activities.csv'
    directory_files_unzip = 'import_strava/activities_unzip/'
    directory_missing_info = 'import_strava/activities_missing_info/'
    directory_wrong_timedelta = 'import_strava/activities_wrong_timedelta'

    # TODO : Some information does not seem to be
    #  present in the real activities (altitude, power ...).

    mandatory_information = [
        'altitude',
        'distance',
        'timestamp',
        'speed',
        'power',
        'position_lat',
        'position_long',
        'heart_rate',
        'cadence']

    def __init__(self):
        self.cycling_fit_files_names = []
        self.files_missing_info = []

    def get_cycling_activities_fit_file(self):
        """
        From the .csv of the summary of Strava's activities only the following are kept :
        - Cycling activities
        - Activities distance != 0
        - .fit files

        We then keep only the name of each of the files.
        """
        df = pd.read_csv(self.activities_full_csv)

        # Take only "Vélo" activities

        # activities_type = df["Type d'activité"].unique()
        # cycling_activity_type = [
        #     activity_type for activity_type in activities_type if 'Vélo' in activity_type
        # ]
        #
        # df_cycling = df.loc[df["Type d'activité"].isin(cycling_activity_type)]

        # TODO We only take Home Trainer activities for the MVP.

        df_cycling = df.loc[df["Type d'activité"] == "Vélo virtuel"]

        # remove activities with a distance = 0
        # Distance is considered as a string
        df_cycling = df_cycling.loc[df_cycling["Distance"] != '0']

        # file name recovery
        cycling_fit_files_names = df_cycling['Nom du fichier'].values

        # Some files are in .gpx, we remove them from the list.
        cycling_fit_files_names = [
            fit_file_name for fit_file_name in cycling_fit_files_names if ".gpx" not in fit_file_name
        ]

        # remove "activities/" from the name of each of the files
        cycling_fit_files_names = [
            fit_file_name.replace('activities/', '') for fit_file_name in cycling_fit_files_names
        ]

        self.cycling_fit_files_names = cycling_fit_files_names
        logging.info(f'Recovery of  {len(self.cycling_fit_files_names)} .fit files')

    def unzip_file(self):
        """
        unzip all .fit files and rename : 15122.fit.gz => 15122.fit
        """
        # If the folder doesn't exist, we create it.
        # If it already exists we delete it and recreate it to avoid errors.

        if not os.path.exists(self.directory_files_unzip):
            os.makedirs(self.directory_files_unzip)
        else:
            shutil.rmtree(self.directory_files_unzip)
            os.makedirs(self.directory_files_unzip)

        i = 0
        for cycling_fit_file_name in self.cycling_fit_files_names:
            with gzip.open(self.directory_files + cycling_fit_file_name, 'r') as f_in, open(
                    self.directory_files_unzip + cycling_fit_file_name.replace('.gz', ''), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            i += 1
        logging.info(f'{i} files have been unzipped')

    def delete_files_missing_info(self):

        """
        Not all files have the same information.
        We want at least
        check that the first point has sufficient information.
        If there is not enough information we delete the files.
        """

        # If the folder doesn't exist, we create it.
        # If it already exists we delete it and recreate it to avoid errors.

        if not os.path.exists(self.directory_missing_info):
            os.makedirs(self.directory_missing_info)
        else:
            shutil.rmtree(self.directory_missing_info)
            os.makedirs(self.directory_missing_info)

        fit_files_unzip = os.listdir(self.directory_files_unzip)

        for fit_file_unzip in fit_files_unzip:
            fit_file_path = self.directory_files_unzip + fit_file_unzip
            fit_parse = fitparse.FitFile(fit_file_path)

            i = 0
            current_information = []

            for record in fit_parse.get_messages("record"):
                if i > 0:
                    break
                for data in record:
                    current_information.append(data.name)
                i += 1

            fit_parse.close()

            check = all(info in current_information for info in self.mandatory_information)

            if not check:
                # TODO: For the moment the files with missing information are just moved,
                #       eventually they will have to be deleted.
                shutil.move(self.directory_files_unzip + fit_file_unzip, self.directory_missing_info)

        logging.info(
            f'Keeping {len(os.listdir(self.directory_files_unzip))} files with'
            f' right information {self.mandatory_information}')
        logging.info(f'Moving {len(os.listdir(self.directory_missing_info))} files with missing information')

    def delete_file_wrong_timedelta(self, desired_average_timedelta):
        """
        Verification of the time difference between two points of a file,
        to see that it is always the same from one file to another.
        If the average timedelta between the first 10 points and
        the last 10 points is not equal to 1 second, delete file
        """

        # If the folder doesn't exist, we create it.
        # If it already exists we delete it and recreate it to avoid errors.

        if not os.path.exists(self.directory_wrong_timedelta):
            os.makedirs(self.directory_wrong_timedelta)
        else:
            shutil.rmtree(self.directory_wrong_timedelta)
            os.makedirs(self.directory_wrong_timedelta)

        fit_files_unzip = os.listdir(self.directory_files_unzip)

        for fit_file in fit_files_unzip:
            fit_file_path = self.directory_files_unzip + fit_file
            fit_parse = fitparse.FitFile(fit_file_path)

            # Take in two lists the first 10 and the last 10 points
            ten_first_elements = list(fit_parse.get_messages("record"))[:10]
            ten_last_elements = list(fit_parse.get_messages("record"))[-10:]

            first_elements_datetime = [
                record.get("timestamp").value for record in ten_first_elements
            ]

            last_elements_datetime = [
                record.get("timestamp").value for record in ten_last_elements
            ]

            fit_parse.close()

            # If the first 10 and the last 10 points have an average difference of 1sec it's correct ,
            # Otherwise we delete them
            if not self.check_average_timedelta(first_elements_datetime, desired_average_timedelta) or \
                    not self.check_average_timedelta(last_elements_datetime, desired_average_timedelta):
                # TODO: For the moment the files with wrong timedelta between 2 points are just moved,
                #       eventually they will have to be deleted.
                shutil.move(self.directory_files_unzip + fit_file, self.directory_wrong_timedelta)

        logging.info(
            f'Keeping {len(os.listdir(self.directory_files_unzip))} files with'
            f' right timedelta ')
        logging.info(f'Moving {len(os.listdir(self.directory_wrong_timedelta))} files with wrong timedelta')

    @staticmethod
    def check_average_timedelta(list_datetime, desired_average_timedelta):

        """
        Checks if all items in a list are spaced at the same timedelta (desired_average_timedelta)
        Return True/False
        """

        timedelta = [list_datetime[i] - list_datetime[i - 1] for i in range(1, len(list_datetime))]
        average_timedelta = sum(timedelta, datetime.timedelta(0)) // len(timedelta)

        if average_timedelta == datetime.timedelta(seconds=desired_average_timedelta):
            return True
        else:
            return False
