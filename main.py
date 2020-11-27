from domain.road import Road

road = Road("./fit_files/alpes.fit")
road.compute_segmentation()
print(road.segmented_records)










# fitfile = fitparse.FitFile("./fit_files/alpes.fit")
# road, road_segmented = segmentation.transform_fit_into_segments(fitfile)
# infos_road = create_dataset.transform_road_to_dataset(road,road_segmented)
#
# columns = ['date','duration','mean_power','mean_speed','mean_heart_rate','mean_cadence','distance','gain_altitude','denivele']
# df = pd.DataFrame(infos_road, columns = columns)
# df = create_dataset.type_previous_segment(df)
#
# print(df)
# create_dataset.debug_strava(df)