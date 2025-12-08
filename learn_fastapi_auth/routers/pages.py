# -*- coding: utf-8 -*-

"""
Page routes for HTML templates.

These routes serve HTML pages using Jinja2 templates.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from learn_fastapi_auth.paths import dir_templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(dir_templates))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the homepage."""
    return templates.TemplateResponse(request, "index.html")


@router.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    """Render the signup page."""
    return templates.TemplateResponse(request, "signup.html")


@router.get("/signin", response_class=HTMLResponse)
async def signin(request: Request):
    """Render the signin page."""
    return templates.TemplateResponse(request, "signin.html")


@router.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    """Render the user app page."""
    return templates.TemplateResponse(request, "app.html")
