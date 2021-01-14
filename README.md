# Prediction of bike travel time

Création de l'environnement

```cmd
conda env create -f environment.yml
```

### Elasticsearch + Kibana
```
docker-compose -f docker-compose.yml up
docker-compose -f docker-compose.yml down
```

### Strava Auth

```
uvicorn app:app --reload --host=0.0.0.0 --port=8090
```

http://localhost:8090/strava_authorize



