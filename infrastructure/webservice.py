import json
import os
import urllib.parse
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse

load_dotenv()
app = FastAPI()


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
    with open('../strava_token.json', 'w') as outfile:
        json.dump(strava_request.json(), outfile)

    return "Récupération des tokens d'accés au compte"


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
    url = f"http://www.strava.com/oauth/authorize?{urllib.parse.urlencode(params)}"
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
        return exchange_token(authorization_code)
