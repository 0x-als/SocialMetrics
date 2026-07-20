from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from telethon.crypto.rsa import encrypt

from database import init_database
from utils import security
from website.core import templates

route = APIRouter()


@route.get("/api/settings/users", response_class=JSONResponse)
async def list_users(request: Request):
    users = await init_database.users_repo.get_all_users()
    return JSONResponse(
        content=[
            {
                "id": user.id,
                "login": user.login,
                "role": user.role.title if user.role else "Без роли",
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M"),
                "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M")
            }
            for user in users
        ]
    )


@route.get("/api/settings/users/roles", response_class=JSONResponse)
async def list_roles(request: Request):
    roles = await init_database.roles_repo.get_all_roles()
    return JSONResponse(
        content=[
            {
                "id": role.id,
                "title": role.title
            }
            for role in roles
            if role.title.lower() != "admin"
        ]
    )


@route.post("/api/settings/users/create", response_class=JSONResponse)
async def create_user(
        request: Request,
        login: str = Form(...),
        password: str = Form(...),
        role_id: int = Form(...)
):
    role = await init_database.roles_repo.get_role_by_id(role_id)

    if not role:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Роль не найдена"
            }
        )

    if role.title.lower() == "admin":
        return JSONResponse(
            status_code=403,
            content={
                "message": "Создание администратора запрещено"
            }
        )

    exists = await init_database.users_repo.get_user_login(login)

    if exists:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Пользователь уже существует"
            }
        )

    user = await init_database.users_repo.create_user(
        login=login,
        password_hash=await security.encrypt(password),
        role_id=role_id
    )

    if not user:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Ошибка создания пользователя"
            }
        )

    return JSONResponse(
        content={
            "status": "ok"
        }
    )


@route.delete("/api/settings/users/{user_id}", response_class=JSONResponse)
async def delete_user(
        request: Request,
        user_id: int
):
    user = await init_database.users_repo.get_user_by_id(user_id)

    if not user:
        return JSONResponse(
            status_code=404,
            content={
                "message": "Пользователь не найден"
            }
        )

    if user.role and user.role.title.lower() == "admin":
        return JSONResponse(
            status_code=403,
            content={
                "message": "Нельзя удалить администратора"
            }
        )

    result = await init_database.users_repo.delete_user(
        user_id
    )

    if not result:
        return JSONResponse(
            status_code=500,
            content={
                "message": "Ошибка удаления"
            }
        )

    return JSONResponse(
        content={
            "status": "ok"
        }
    )
