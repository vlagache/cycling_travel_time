from domain.road import Road
from domain.segment import Segment

if __name__ == "__main__":

    road = Road(fit_file="./fit_files/alpes.fit")
    road.parsing_from_fit_file()
    segments_schedule = road.compute_segmentation()

    segments_of_a_road = []
    for i in range(len(segments_schedule)):
        # First segment of road
        # We take the points between the beginning
        # and the end of the segment
        if i == 0:
            all_points_segment_df = road.get_all_points_of_one_segment(
                records=road.records,
                start=segments_schedule[f'segment_{i}']['start'],
                end=segments_schedule[f'segment_{i}']['end'])
            segment = Segment(all_points_segment_df)
            segment.compute_metrics(first_segment=True)
            segments_of_a_road.append(segment)

        # For all other segments
        # We take the points between the end of the segment
        # and the end of the previous segment.
        else:
            all_points_segment_df = road.get_all_points_of_one_segment(
                records=road.records,
                start=segments_schedule[f'segment_{i - 1}']['end'],
                end=segments_schedule[f'segment_{i}']['end'])
            segment = Segment(all_points_segment_df)
            segment.compute_metrics()
            segments_of_a_road.append(segment)

    road = Road(segments=segments_of_a_road)
    road.compute_type_previous_segment()
    road.debug_strava()

    # # injection at the base of each segment
    # for segment in road.segments:
    #     print(segment.type_previous_segment)
    # insert in BDD ...
