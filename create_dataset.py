import numpy as np
import warnings
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'


def transform_road_to_dataset(road,road_segmented):
    '''
    Takes two dataframes as an input
    road : dataframe of all the points of a .fit
    road_segmented : dataframe with a point every x seconds on which segments have been calculated

    Returns a dataframe in which a line = a segment with all the information associated with this segment (distance, average speed etc...).
    '''
    
    #Création d'un dataframe avec le début et la fin de chaque segment
    start_end_segments = road_segmented.groupby('segment').agg(['first','last']).stack()

    infos_road = []
    for i in range(len(start_end_segments.xs('first',level=1))):

        # Logique pour le premier segment:
        if i == 0:
            all_points_segment = road[road['timestamp'].between(start_end_segments.xs('first',level=1)['timestamp'][i], start_end_segments.xs('last',level=1)['timestamp'][i])]
            all_points_segment['timestamp'] = pd.to_datetime(all_points_segment['timestamp'])
            date = pd.to_datetime(all_points_segment['timestamp'].head(1).values[0]).date()
            duration = (all_points_segment['timestamp'].tail(1).values[0] - all_points_segment['timestamp'].head(1).values[0]) / np.timedelta64(1,'s')

            mean_power = round(all_points_segment['power'].mean(),2)
            mean_speed = round(all_points_segment['speed'].mean()*3.6,2)
            mean_heart_rate = round(int(all_points_segment['heart_rate'].mean()),2)
            mean_cadence = round(int(all_points_segment['cadence'].mean()),2)
            gain_altitude = round((all_points_segment.tail(1)['altitude'].values[0] - all_points_segment.head(1)['altitude'].values[0]),2)
            distance = all_points_segment.tail(1)['distance'].values[0]
            denivele  = round(((gain_altitude * 100 ) / distance),2)

            infos_segment = []
            infos_segment.extend((date,duration,mean_power,mean_speed,mean_heart_rate,mean_cadence,distance,gain_altitude,denivele))
            infos_road.append(infos_segment)
        
        # Logique pour tout les autres segments
        else:
            # Tout les autres segments on prend entre fin n-1 et fin n 
            all_points_segment = road[road['timestamp'].between(start_end_segments.xs('last',level=1)['timestamp'][i-1], start_end_segments.xs('last',level=1)['timestamp'][i])]
            all_points_segment['timestamp'] = pd.to_datetime(all_points_segment['timestamp'])
            date = pd.to_datetime(all_points_segment['timestamp'].head(1).values[0]).date()
            duration = (all_points_segment['timestamp'].tail(1).values[0] - all_points_segment['timestamp'].head(1).values[0]) / np.timedelta64(1,'s')

            mean_power = round(all_points_segment['power'].mean(),2)
            mean_speed = round(all_points_segment['speed'].mean()*3.6,2)
            mean_heart_rate = round(int(all_points_segment['heart_rate'].mean()),2)
            mean_cadence = round(int(all_points_segment['cadence'].mean()),2)
            gain_altitude = round((all_points_segment.tail(1)['altitude'].values[0] - all_points_segment.head(1)['altitude'].values[0]),2)
            distance= round((all_points_segment.tail(1)['distance'].values[0] - all_points_segment.head(1)['distance'].values[0]),2)
            denivele  = round(((gain_altitude * 100 ) / distance),2)

            infos_segment = []
            infos_segment.extend((date,duration,mean_power,mean_speed,mean_heart_rate,mean_cadence,distance,gain_altitude,denivele))
            infos_road.append(infos_segment)

    return infos_road


def type_previous_segment(df):
    '''
    Takes a dataframe as an input summarizing a road
    Adds a column comparing the altitude gain of the previous segment to define its type.
    Ex gain_altitude n-1 = -50 , the previous segment was a descent

    Return a dataframe with 'type_previous' column added
    '''
    for i in range(len(df)):
        if i == 0:
            df.loc[i,'type_previous'] = 'start'
        # descente
        elif df.loc[i-1,'gain_altitude'] < 0 :
            df.loc[i,'type_previous'] = 'downhill'
        elif df.loc[i-1,'gain_altitude'] > 0 :
            df.loc[i,'type_previous'] = 'uphill'
        else:
            df.loc[i,'type_previous'] = 'flat'
    return df

def debug_strava(df):
    '''
    Debug function to check that the transformation
    of a route corresponds with Strava's information.
    '''
    total_duration = df['duration'].sum()
    total_distance = df['distance'].sum()
    mean_speed = ((total_distance*3600) / total_duration)/1000


    print(f'Durée totale(sec) : {total_duration}')
    print(f'Distance totale(km) : {(total_distance/1000).round(2)}')
    print(f'Vitesse moyenne(km/h): {(mean_speed).round(2)}')



