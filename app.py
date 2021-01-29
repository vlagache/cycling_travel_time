import logging
import os
import urllib.parse
from typing import Optional

import gpxpy
import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Cookie, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from domain import athlete
from infrastructure.adapter_data import AdapterAthlete
from infrastructure.elasticsearch import ElasticAthleteRepository
from infrastructure.elasticsearch import Elasticsearch
from infrastructure.import_strava import ImportStrava

logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.DEBUG)

load_dotenv()
app = FastAPI()
elasticsearch = Elasticsearch(local_connect=True)
LOGIN_URL = "http://www.strava.com/oauth/authorize"

athlete.repository = ElasticAthleteRepository()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/images", StaticFiles(directory="images"), name="images")
templates = Jinja2Templates(directory="templates")


################# DEBUG


@app.get("/debug")
async def debug():
    info_activities = elasticsearch.retrieve_general_info_on_activities()
    return info_activities


@app.get("/route")
async def route(access_token: str = Cookie(None),
                refresh_token: str = Cookie(None),
                token_expires_at: str = Cookie(None),
                user_id: str = Cookie(None)):
    import_strava = ImportStrava(access_token=str(access_token),
                                 refresh_token=str(refresh_token),
                                 token_expires_at=int(token_expires_at),
                                 user_id=str(user_id),
                                 dao=elasticsearch)

    return import_strava.store_all_routes_athlete()


@app.get("/get_route")
async def get_route():
    route_test = elasticsearch.get_doc_by_id(index_name="index_route",
                                             id_data=2787335981548134218)
    gpx = gpxpy.parse(route_test['gpx_file'])
    data = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                data.append([point.latitude, point.longitude, point.elevation])
    df = pd.DataFrame(data, columns=['latitude', 'longitude', 'elevation'])
    print(df)


###################


@app.get("/", response_class=HTMLResponse)
async def check_user(request: Request):
    return templates.TemplateResponse("check_user.html", {"request": request})


@app.post("/")
async def check_user(firstname: str = Form(...),
                     lastname: str = Form(...)):
    athlete_ = athlete.repository.check_if_exist(firstname, lastname)
    if athlete_ is not None:
        response = RedirectResponse("/authenticated_user", status_code=302)
        response.set_cookie(key="access_token", value=athlete_.access_token)
        response.set_cookie(key="refresh_token", value=athlete_.refresh_token)
        response.set_cookie(key="token_expires_at", value=str(athlete_.token_expires_at))
        response.set_cookie(key="user_id", value=str(athlete_.id))
        return response
    else:
        return RedirectResponse("/auth", status_code=302)


@app.get("/auth", response_class=HTMLResponse)
async def main(request: Request):
    ### Template pour s'authentifier
    return templates.TemplateResponse("auth.html", {"request": request})


@app.get("/authenticated_user", response_class=HTMLResponse)
async def authenticated_user(request: Request,
                             access_token: str = Cookie(None),
                             refresh_token: str = Cookie(None),
                             token_expires_at: str = Cookie(None),
                             user_id: str = Cookie(None)
                             ):
    import_strava = ImportStrava(access_token=str(access_token),
                                 refresh_token=str(refresh_token),
                                 token_expires_at=int(token_expires_at),
                                 user_id=str(user_id),
                                 dao=elasticsearch)

    info_activities = elasticsearch.retrieve_general_info_on_activities()
    info_routes = elasticsearch.retrieve_general_info_on_routes()

    return templates.TemplateResponse("authenticated_user.html",
                                      {"request": request,
                                       "import_strava": import_strava,
                                       "info_activities": info_activities,
                                       "info_routes": info_routes})


#############

@app.get("/get_new_activities")
async def get_new_activities(access_token: str = Cookie(None),
                             refresh_token: str = Cookie(None),
                             token_expires_at: str = Cookie(None),
                             user_id: str = Cookie(None)):
    import_strava = ImportStrava(access_token=str(access_token),
                                 refresh_token=str(refresh_token),
                                 token_expires_at=int(token_expires_at),
                                 user_id=str(user_id),
                                 dao=elasticsearch)

    activities_added = import_strava.storage_of_new_activities()
    info_activities = elasticsearch.retrieve_general_info_on_activities()
    info_activities['activities_added'] = activities_added
    return info_activities


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
        # Athlete
        athlete_ = AdapterAthlete(response_strava).get()
        athlete.repository.save(athlete_)

        response = RedirectResponse("/authenticated_user")
        response.set_cookie(key="access_token", value=athlete_.access_token)
        response.set_cookie(key="refresh_token", value=athlete_.refresh_token)
        response.set_cookie(key="token_expires_at", value=str(athlete_.token_expires_at))
        response.set_cookie(key="user_id", value=str(athlete_.id))

        return response
