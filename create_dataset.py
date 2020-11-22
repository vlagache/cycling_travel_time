import numpy as np
import warnings
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'


# Fonction qui prend 2 deux dataframe en entrée 
# - Parcours complet , point toutes les secondes
# - Parcours ségmenté point toutes les 20 secondes
# Return un dataframe avec les segments et leurs infos

def transform_road_to_dataset(road,road_segmented):
    
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


    
road_segmented = pd.read_csv('csv/alpes_segmented.csv',index_col=0)
road = pd.read_csv('csv/alpes.csv',index_col=0)
infos_road = transform_road_to_dataset(road,road_segmented)

columns = ['date','duration','mean_power','mean_speed','mean_heart_rate','mean_cadence','distance','gain_altitude','denivele']
df = pd.DataFrame(infos_road, columns = columns)
df = type_previous_segment(df)

print(df)

# Verif Strava
total_duration = df['duration'].sum()
total_distance = df['distance'].sum()
mean_speed = ((total_distance*3600) / total_duration)/1000


print(total_duration)
print((total_distance/1000).round(2))
print((mean_speed).round(2))



