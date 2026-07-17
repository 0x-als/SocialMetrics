from datetime import date
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse

from database import init_database
from website.core import templates

route = APIRouter()


@route.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html"
    )


@route.get("/api/dashboard/circle_metrics", response_class=HTMLResponse)
async def api_dashboard_circle_metrics(request: Request):
    stats = await init_database.metrics_repo.get_circle_last_metrics()
    return templates.TemplateResponse(
        request=request,
        name="circle_metrics.html",
        context={
            "request": request,
            "stats": stats
        }
    )


@route.get("/api/dashboard/line_metrics", response_class=HTMLResponse)
async def line_metrics(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="line_metrics.html"
    )


@route.get("/api/dashboard/line_metrics/data", response_class=JSONResponse)
async def line_metrics_data(
        user_id: int = Query(...),
        type: str = Query(..., pattern="^(instagram|tiktok|youtube|telegram|vk)$"),
        metric: str = Query(..., pattern="^(likes|views_picture|views_video|saves|reposts|comments_count)$"),
        date_from: date = Query(...),
        date_to: date = Query(...)
):
    data = await init_database.metrics_repo.get_line_metrics(
        user_id=user_id,
        type=type,
        metric=metric,
        date_from=date_from,
        date_to=date_to
    )

    return JSONResponse(content=data)



@route.get("/api/dashboard/list_social_networks", response_class=JSONResponse)
async def api_dashboard_list_social_networks(request: Request):
    users = await init_database.social_networks_repo.get_users_for_line_metrics()
    return JSONResponse(content=users)
