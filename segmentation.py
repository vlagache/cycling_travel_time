import pandas as pd
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings('ignore')




def sign_equal(a,b):
    '''
    Compares the two-digit sign and indicates whether they are identical
    Takes the 0 as a separate value 
    ex : sign_equal(0,-5) >>> False
    Return True/False
    '''
    return np.sign(a) == np.sign(b)

def segmentation(df):
    '''
    Takes a dataframe from a .fit with an altitude_gain column as an input.
    altitude_gain for n equals the difference in altitude between n and n-1

    Calculation of the logical segments (ascent, flat, descent) as a function of altitude gain. 
    Compare for each line the altitude gain sign n & n-1.

    Same sign, same segment (ex 8 and 5, same ascent segment)
    Change of sign change of segment (ex 8 and -5, from a downhill segment to an uphill segment)

    Special case for zeros : 
    if n = 0 et n-1 != 0 : same segment
    In case of a succession of zeros ( from two ): flat segment

    Returns a dataframe with a segment column
    '''
    for i in range(len(df['altitude_gain'])):
        
        # premiere ligne on démarre au segment zero
        if i == 0:
            df.loc[i,"segment"] = 0
        
        # pour toutes les autres lignes
        else: 
            
            # si n et n-1 ont le meme signe....
            if sign_equal(df.loc[i,"altitude_gain"],df.loc[i-1,"altitude_gain"]):
                
                # dans le cas ou n et n-1 valent zéro....
                if df.loc[i,'altitude_gain'] == 0 and df.loc[i-1,'altitude_gain'] == 0 :
                    
                    # si n-2 n'est pas égal a zero
                    # Segment de plat , on veut faire un nouveau segment , et changer retrospectivement
                    # le segment de n-1 qui n'est plus un zéro "tout seul"
                    if df.loc[i-2,'altitude_gain'] != 0:
                        df.loc[i, "segment"] = df.loc[i-1, "segment"] + 1 
                        df.loc[i-1, "segment"] = df.loc[i-1, "segment"] + 1
                    # si n , n-1 , n-2 = 0 , on ne veut pas changer de segment
                    # Succession de zero
                    else:
                        df.loc[i, "segment"] = df.loc[i-1, "segment"]
                # Si meme signe sans cas particulier , meme segment
                else:
                    df.loc[i, "segment"] = df.loc[i-1, "segment"]
                
            # Si pas meme signe 
            else:
#                 # si abs(n) - abs(n-1) < 0 .5 , on conserve dans le meme segment
#                 if abs(df.loc[i,'altitude_gain']) - abs(df.loc[i-1,'altitude_gain']) < 0.5:
#                     df.loc[i, "segment"] = df.loc[i-1, "segment"]
                # si n = 0 et n-1 !=0 , on conserve un seul zero dans le segment existant
                if df.loc[i,'altitude_gain'] == 0 and df.loc[i-1,'altitude_gain'] != 0 :
                    df.loc[i, "segment"] = df.loc[i-1, "segment"]
                # Sinon on change de segment
                else:
                    df.loc[i, "segment"] = df.loc[i-1, "segment"] + 1  
    return df

def transform_fit_into_segments(fitfile):

    '''
    takes a fitfile at input
    returns a dataframe formatting the fitfile information ( all the dots )
    and a dataframe with same informations + the segments (with a dot every x seconds).
    '''

    # récuperation des distances
    distances = []
    for record in fitfile.get_messages("record"):
        for data in record:
            if data.name == 'distance':
                if data.value is not None:
                    distances.append(data.value)

    # recupération des enregistrements point par point
    records = []
    for record in fitfile.get_messages("record"):
        records.append(record.get_values())

    df = pd.DataFrame(records)
    df = df.drop(['distance','time_from_course','compressed_speed_distance','enhanced_altitude','enhanced_speed','grade','resistance','cycle_length','temperature'], axis='columns')

    # On prend un point toutes les 20 secondes pour réduire la taille du dataframe
    df_every_20_sec = df.iloc[::20, :]
    df_every_20_sec = df_every_20_sec.reset_index(drop=True)

    # Calcul des différences d'altitude n & n-1
    altitude_gain = [np.nan]
    for i in range(df_every_20_sec.shape[0]):
        if i > 0:
            altitude_gain.append(df_every_20_sec['altitude'][i]-df_every_20_sec['altitude'][i-1])


    df_every_20_sec['altitude_gain'] = altitude_gain

    #On conserve la premiere valeur avec une altitude NaN
    is_NaN = df_every_20_sec.isnull()
    row_has_NaN = is_NaN.any(axis=1)
    df_nan_values = df_every_20_sec[row_has_NaN]
    df_nan_values['segment'] = 0

    # # On enleve la premiere valeur qui a un gain d'altitude nul ( pas de point avec lequel comparer)
    df_every_20_sec = df_every_20_sec.dropna()
    df_every_20_sec = df_every_20_sec.reset_index(drop=True)

    df_every_20_sec = segmentation(df_every_20_sec)
    # on rajoute la premiere valeur qu'on avait enlenvé
    df_every_20_sec = df_nan_values.append(df_every_20_sec,ignore_index=True)

    # on save le df initial et celui segmenté
    df.to_csv("csv/alpes.csv")
    df_every_20_sec.to_csv("csv/alpes_segmented.csv")