import os
import urllib.parse
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Cookie, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, Response

from infrastructure.elasticsearch import Elasticsearch

load_dotenv()
app = FastAPI()

LOGIN_URL = "http://www.strava.com/oauth/authorize"

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")
templates = Jinja2Templates(directory="templates")


############# TEST DEBUG


def get_current_token(access_token: str = Cookie(None)):
    if not access_token:
        return None
    else:
        return access_token


@app.get("/auth", response_class=HTMLResponse)
async def main(request: Request, access_token=Depends(get_current_token)):

    if not access_token:
        ### Template pour s'authentifier
        return templates.TemplateResponse("auth.html", {"request": request})
    else:
        #### Template pour Charger les activités etc...
        return access_token


@app.get("/", response_class=HTMLResponse)
async def check_user(request: Request):
    return templates.TemplateResponse("check_user.html", {"request": request})


@app.post("/")
async def check_user(first_name: str = Form(...),
                     last_name: str = Form(...)):
    elasticsearch = Elasticsearch(local_connect=True)
    if elasticsearch.check_if_user_exist(first_name, last_name):
        # TODO : On recupere les infos en base qu'on set en cookie ?
        return "User exist"
    else:
        return RedirectResponse("/auth", status_code=302)

    # if check_if_user_exist(first_name,last_name):
    #     # On recupere ses tokens
    #     if token_still_valid:
    #         redirect to /loading_activity
    #     else:
    #         refresh_token
    # else:
    #     redirect to /auth
    #


#############


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
async def strava_token(response: Response, code: Optional[str] = None):
    """
    Request for an access token limited to the user account
    in exchange for the authorization code.
    """
    authorization_code = code
    if not authorization_code:
        raise HTTPException(status_code=400, detail="Missing code param")
    else:
        response_strava = exchange_token(authorization_code)
        elasticsearch = Elasticsearch(local_connect=True)
        elasticsearch.store_data(
            data_json=response_strava,
            index_name="index_user",
            id_data=response_strava['athlete']['id']
        )
        access_token = response_strava['access_token']
        response = RedirectResponse("/auth")
        #TODO : set cookie refresh token , expire at ?

        response.set_cookie(key="access_token", value=str(access_token))
        return response
