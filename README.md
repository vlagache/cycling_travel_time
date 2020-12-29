# Prediction of bike travel time

Création de l'environnement

```cmd
conda env create -f environment.yml
```


### Strava Auth

```
cd infrastructure
uvicorn webservice:app --reload --host:0.0.0.0 --port=8090
```

http://localhost:8090/strava_authorize



