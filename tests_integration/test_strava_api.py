import unittest
from dotenv import load_dotenv
from elasticmock import elasticmock


from prediction.infrastructure.adapter_data import AdapterAthlete
from prediction.infrastructure.elasticsearch import ElasticAthleteRepository
from prediction.domain import athlete
from prediction.infrastructure.import_strava import ImportStrava


class TestStravaApi(unittest.TestCase):

    # SCHEMA : https://www.liquid-technologies.com/online-json-to-schema-converter

    @elasticmock
    def setUp(self) -> None:
        load_dotenv()
        athlete.repository = ElasticAthleteRepository()

    def test_something(self):
        athlete_dict = {
            "athlete": {
                "id": 10944546,
                "firstname": "BLABLABLA",
                "lastname": "Lagache"
            },
            "refresh_token": "233b95bcd263ba5be460484c96aed2ca76d025a3",
            "access_token": "daa0fb5e6dd40e4e0e03fc7645c92786760a8d4c",
            "expires_at": 1616194664
        }
        athlete_ = AdapterAthlete(athlete_dict).get()
        athlete.repository.save(athlete_)
        athlete_ = athlete.repository.get(10944546)
        import_strava = ImportStrava(athlete_)
        result = import_strava.get_all_activities_ids()
        print(len(result))
        print(result)






### connection api strava with token athlete...
### validate contract route / activities / athlete ?
