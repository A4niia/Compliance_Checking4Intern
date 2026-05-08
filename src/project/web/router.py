from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# from myqueue import p1_extract_job_post, hello
# from myqueue import app as celery_app
# from celery.result import AsyncResult
import os

_BUILD_VERSION:str = os.environ["BUILD_VERSION"]

router = APIRouter()
# router.mount("/static", StaticFiles(directory="static"), name="static")

template_path = Path(__file__).parent.joinpath("templates")
templates = Jinja2Templates(directory=template_path)


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    context = {"build_version":_BUILD_VERSION}
    return templates.TemplateResponse(request=request, name="index.html", context=context)

@router.get("/example/{id}", response_class=HTMLResponse)
async def get_example(request: Request, id:int):
    return templates.TemplateResponse(request=request, name="example.html", context={"id":id})