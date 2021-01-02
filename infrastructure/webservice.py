import os
import urllib.parse
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Cookie, Depends, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

load_dotenv()
app = FastAPI()

LOGIN_URL = "http://www.strava.com/oauth/authorize"

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")
templates = Jinja2Templates(directory="templates")


############# TEST DEBUG


def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        return None
    else:
        return "???"
        # data = decrypt(session)  # some cryptography decryption
        # user = query_user(data["user"])  # Query user
        # return user


@app.get("/", response_class=HTMLResponse)
async def main(request: Request, current_user=Depends(get_current_user)):
    already_auth = False
    if not current_user:
        return templates.TemplateResponse("test.html", {"request": request, "auth": already_auth})
    else:
        return current_user


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

    # with open('../strava_token.json', 'w') as outfile:
    #     json.dump(strava_request.json(), outfile)
    #
    # return "Récupération des tokens d'accés au compte"


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
        return response_strava
        # response.set_cookie(key="session", value=response_strava)
        # return RedirectResponse("/", status_code=302)

        # On verifie si un utilisateur avec le meme id existe dans la base de données
        # SI Oui on récupérere son access_token => Cookie
        # Si Non on l'inscrit en base , et son access_token => Cookie

# @app.get("/set_cookie")
# async def strava_token(response: Response, session: str = Cookie(None)):
#     print(session)
#     dict_test = {
#         "token": 124568,
#         "refresh_token": 56646541654
#     }
#     response.set_cookie(key="session", value=dict_test)
