import os
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from models import User
from routers.auth import get_current_user

router = APIRouter(prefix="/auth/google", tags=["auth"])

# In a real app, these come from your Google Cloud Console JSON
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", "your-id"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "your-secret"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8000/api/v1/auth/google/callback"],
    }
}

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

@router.get("/login")
def google_login():
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0]
    )
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return RedirectResponse(auth_url)

@router.get("/callback")
def google_callback(
    code: str
):
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0]
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # In a real app, find the user from session/state (Using Beanie async methods)
    # await User.find_one(...)
    
    print(f"DEBUG: Successfully fetched Google Token: {credentials.token[:10]}...")
    return RedirectResponse("http://localhost:3000/dashboard?sync=success")
