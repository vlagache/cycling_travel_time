import os
import time
import urllib.parse
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Cookie, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from prediction.domain import athlete, activity, route, model, predict
from prediction.domain.model import TypeModel
from prediction.infrastructure.adapter_data import AdapterAthlete
from prediction.infrastructure.elasticsearch import \
    ElasticAthleteRepository, ElasticActivityRepository, ElasticRouteRepository, ElasticModelRepository
from prediction.infrastructure.import_strava import ImportStrava

load_dotenv()
app = FastAPI()

origins = [
    "http://localhost:8090"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOGIN_URL = "http://www.strava.com/oauth/authorize"

athlete.repository = ElasticAthleteRepository()
activity.repository = ElasticActivityRepository()
route.repository = ElasticRouteRepository()
model.repository = ElasticModelRepository()

app.mount("/static", StaticFiles(directory="prediction/infrastructure/static"), name="static")
app.mount("/js", StaticFiles(directory="prediction/infrastructure/js"), name="js")
app.mount("/images", StaticFiles(directory="prediction/infrastructure/images"), name="images")
templates = Jinja2Templates(directory="prediction/infrastructure/templates")


################# DEBUG

@app.get("/virtual_ride")
async def get_prediction(var: bool, test=int):
    if var:
        return f"Virtual Ride{test}"
    else:
        return f"Real Ride{test}"


###################


@app.get("/", response_class=HTMLResponse)
async def check_user(request: Request):
    return templates.TemplateResponse("connexion.html", {"request": request})


@app.post("/")
async def check_user(firstname: str = Form(...),
                     lastname: str = Form(...)):
    athlete_ = athlete.repository.search_if_exist(firstname, lastname)
    if athlete_ is not None:
        response = RedirectResponse("/authenticated_user", status_code=302)
        response.set_cookie(key="athlete_id", value=str(athlete_.id))
        return response
    else:
        return RedirectResponse("/auth", status_code=302)


@app.get("/auth", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@app.get("/authenticated_user", response_class=HTMLResponse)
async def authenticated_user(request: Request,
                             athlete_id: str = Cookie(None)):
    athlete_ = athlete.repository.get(athlete_id)
    info_activities = activity.repository.get_general_info()
    info_routes = route.repository.get_general_info()
    info_models = model.repository.get_general_info()

    return templates.TemplateResponse("authenticated_user.html",
                                      {"request": request,
                                       "athlete": athlete_,
                                       "info_activities": info_activities,
                                       "info_routes": info_routes,
                                       "info_models": info_models})


@app.get("/road_prediction", response_class=HTMLResponse)
async def road_prediction(request: Request):
    routes = route.repository.get_all_desc()
    return templates.TemplateResponse("road_prediction.html", {"request": request,
                                                               "routes": routes})


#############

@app.get("/get_new_activities")
async def get_new_activities(athlete_id: str = Cookie(None)):
    athlete_ = athlete.repository.get(athlete_id)
    import_strava = ImportStrava(athlete_)
    activities_added = import_strava.storage_of_new_activities()
    info_activities = activity.repository.get_general_info()
    info_activities['activities_added'] = activities_added
    return info_activities


@app.get("/get_new_routes")
async def get_new_routes(athlete_id: str = Cookie(None)):
    athlete_ = athlete.repository.get(athlete_id)
    import_strava = ImportStrava(athlete_)
    routes_added = import_strava.storage_of_new_routes()
    info_routes = route.repository.get_general_info()
    info_routes['routes_added'] = routes_added
    return info_routes


@app.get("/train_models")
async def train_models():
    if activity.repository.is_empty():
        # TODO: Very ugly method to avoid flashing on frontend
        #  The response is too fast which does not allow time
        #  for the loading screen to appear
        time.sleep(3)
        return None
    else:
        for type_model in TypeModel:
            model_ = model.Model(model=type_model)
            model_.train()
            model.repository.save(model_)

        info_models = model.repository.get_general_info()
        return info_models


@app.get("/get_prediction")
async def get_prediction(route_id: int, virtual_ride: bool):
    if model.repository.is_empty():
        return None
    else:
        route_ = route.repository.get(route_id)
        model_ = model.repository.get_better_mape()
        predict_ = predict.Predict(model=model_,
                                   route=route_,
                                   virtual_ride=virtual_ride)
        return predict_.get_prediction()


@app.get("/get_map")
async def get_map(route_id: int):
    route_ = route.repository.get(route_id)
    return route_.get_map()


@app.get("/get_segmentation_map")
async def get_segmentation_map(route_id: int):
    route_ = route.repository.get(route_id)
    return route_.get_segmentation_map()


@app.get("/get_segmentation")
async def get_segmentation(route_id: int):
    route_ = route.repository.get(route_id)
    return route_.segmentation


############
def exchange_token(authorization_code):
    strava_request = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': os.getenv("STRAVA_CLIENT_ID"),
            'client_secret': os.getenv("STRAVA_CLIENT_SECRET"),
            'code': authorization_code,
            'grant_type': 'authorization_code'
        }
    )
    return strava_request.json()


@app.get("/strava_authorize")
async def strava_authorize():
    """
    Application access request to the Strava user page
    Redirects to the /strava_token url with an access code in the answer

    """
    params = {
        'client_id': os.getenv("STRAVA_CLIENT_ID"),
        'response_type': 'code',
        'redirect_uri': 'http://localhost:8090/strava_token',
        'approval_prompt': 'force',
        'scope': 'read,profile:read_all,activity:read_all'
    }
    url = f"{LOGIN_URL}?{urllib.parse.urlencode(params)}"
    response = RedirectResponse(url=url)
    return response


@app.get("/strava_token")
async def strava_token(code: Optional[str] = None):
    """
    Request for an access token limited to the user account
    in exchange for the authorization code.
    """
    authorization_code = code
    if not authorization_code:
        raise HTTPException(status_code=400, detail="Missing code param")
    else:
        response_strava = exchange_token(authorization_code)
        athlete_ = AdapterAthlete(response_strava).get()
        athlete.repository.save(athlete_)

        response = RedirectResponse("/authenticated_user")
        response.set_cookie(key="athlete_id",
                            value=str(athlete_.id),
                            samesite="Strict")

        return response
