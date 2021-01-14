import os
import urllib.parse
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Cookie, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from infrastructure.elasticsearch import Elasticsearch

load_dotenv()
app = FastAPI()

LOGIN_URL = "http://www.strava.com/oauth/authorize"

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")
templates = Jinja2Templates(directory="templates")


############# TEST DEBUG

@app.get("/debug")
async def debug():
    first_name = "Vincent"
    last_name = "Lagache"
    elasticsearch = Elasticsearch(local_connect=True)
    if elasticsearch.check_if_user_exist(first_name, last_name):
        user = elasticsearch.search_user(first_name, last_name)
        access_token = user["_source"]["access_token"]
        refresh_token = user["_source"]["refresh_token"]
        token_expires_at = user["_source"]["expires_at"]
        user_id = user["_id"]
        return f'{access_token} , {refresh_token}, {token_expires_at}, {user_id}'
    else:
        return "pas d'utilisateur a ce nom"


@app.get("/", response_class=HTMLResponse)
async def check_user(request: Request):
    return templates.TemplateResponse("check_user.html", {"request": request})


@app.post("/")
async def check_user(first_name: str = Form(...),
                     last_name: str = Form(...)):
    elasticsearch = Elasticsearch(local_connect=True)
    if elasticsearch.check_if_user_exist(first_name, last_name):

        user = elasticsearch.search_user(first_name, last_name)
        response = RedirectResponse("/authenticated_user", status_code=302)
        response.set_cookie(key="access_token", value=str(user["_source"]["access_token"]))
        response.set_cookie(key="refresh_token", value=str(user["_source"]["refresh_token"]))
        response.set_cookie(key="token_expires_at", value=str(user["_source"]["expires_at"]))
        response.set_cookie(key="user_id", value=str(user["_id"]))
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

    return templates.TemplateResponse("authenticated_user.html",
                                      {"request": request,
                                       "access_token": access_token,
                                       "refresh_token": refresh_token,
                                       "token_expires_at": token_expires_at,
                                       "user_id": user_id})


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
        elasticsearch = Elasticsearch(local_connect=True)
        user_id = elasticsearch.store_data(
            data_json=response_strava,
            index_name="index_user",
            id_data=response_strava['athlete']['id']
        )

        response = RedirectResponse("/authenticated_user")
        response.set_cookie(key="access_token", value=str(response_strava['access_token']))
        response.set_cookie(key="refresh_token", value=str(response_strava['refresh_token']))
        response.set_cookie(key="token_expires_at", value=str(response_strava['expires_at']))
        response.set_cookie(key="user_id", value=str(user_id))

        return response
