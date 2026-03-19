# from re import sub
# from fastapi import Depends, FastAPI , Body
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from migration_tools import create_autogen_migration, upgrade_head
# app = FastAPI()

# bearer_scheme = HTTPBearer()
# from fastapi import FastAPI, Request , HTTPException
# from httpx import request
# from database import SessionLocal
# import models
# from fastapi import HTTPException
# from security import ACCESS_TOKEN_EXPIRE_MINUTES, hash_password
# from security import verify_password
# from security import decode_token
# from jose import JWTError
# from security import create_access_token, create_refresh_token
# app = FastAPI()


# EXCLUDED_PATHS = {
#     "/login",
#     "/users",            
#     "/refresh",         
#     "/openapi.json",
#     "/docs",
#     "/redoc"
# }

# from fastapi.responses import JSONResponse

# @app.middleware("http")
# async def jwt_auth_middleware(request: Request, call_next):

#     if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
#         return await call_next(request)

#     auth_header = request.headers.get("Authorization")

#     if not auth_header or not auth_header.startswith("Bearer "):
#         return JSONResponse(
#             status_code=401,
#             content={"detail": "Invalid or missing token"}
#         )

#     token = auth_header.split(" ")[1]

#     try:
#         payload = decode_token(token)

#         if payload.get("type") != "access":
#             return JSONResponse(
#                 status_code=401,
#                 content={"detail": "Invalid token type"}
#             )

#         sub = payload.get("sub")
#         if sub is None:
#             return JSONResponse(
#                 status_code=401,
#                 content={"detail": "Invalid token payload"}
#             )

#         request.state.user_id = int(sub)

#     except JWTError:
#         return JSONResponse(
#             status_code=401,
#             content={"detail": "Invalid or expired token"}
#         )

#     return await call_next(request)


# @app.post("/users")
# def create_user(name: str, password: str):
#     db = SessionLocal()
#     hashed_password = hash_password(password) 
#     new_user = models.User(name=name, password=hashed_password)
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     db.close()
#     return {"id": new_user.id, "name": new_user.name}


# @app.post("/login")
# def login_user(name: str, password: str):
#     db = SessionLocal()
    
#     user = db.query(models.User).filter(models.User.name==name).first()
    
#     if not user:
#         db.close()
#         raise HTTPException(status_code=404, detail="User not found")
    
#     if  not verify_password(password,user.password):
#         db.close()
#         raise HTTPException(status_code=401, detail="Incorrect password")
    
#     db.close()
    
#     access_token = create_access_token({"sub": str(user.id)})
#     refresh_token = create_refresh_token({"sub": str(user.id)})
#     return {
#         "message": "Login successfully",
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "user_id" : user.id,
#         "token_type": "Bearer",
#     }
        
# @app.get("/me", dependencies=[Depends(bearer_scheme)])
# def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
#     token = credentials.credentials
#     payload = decode_token(token)

#     if payload.get("type") != "access":
#         raise HTTPException(status_code=401, detail="Invalid token")

#     return int(payload.get("sub"))


# @app.post("/tasks", dependencies=[Depends(bearer_scheme)])
# def create_task(request: Request, description: str, status: str, assignee_id: int = None):
#     db = SessionLocal()
#     current_user_id = request.state.user_id

    
#     user = db.query(models.User).filter(
#         models.User.id == current_user_id
#     ).first()

#     if not user:
#         db.close()
#         raise HTTPException(status_code=404, detail="Authenticated user not found")

   
#     if assignee_id:
#         assignee = db.query(models.User).filter(
#             models.User.id == assignee_id
#         ).first()

#         if not assignee:
#             db.close()
#             raise HTTPException(status_code=404, detail="Assignee not found")

   
#     new_task = models.Task(
#         user_id=current_user_id,
#         description=description,
#         status=status,
#         assignee_id=assignee_id
#     )

#     db.add(new_task)
#     db.commit()
#     db.refresh(new_task)
#     db.close()

   
#     return {
#         "id": new_task.id,
#         "user_id": new_task.user_id,  # FIXED
#         "description": new_task.description,
#         "status": new_task.status,
#         "assignee_id": new_task.assignee_id
#     }
# #list of users
# @app.get("/users/list")
# def get_users():
#     db = SessionLocal()
#     users = db.query(models.User).all()
#     db.close()
#     return [
#         {"user_id": user.id, "name": user.name}
#         for user in users
#     ]
# @app.post("/refresh")
# def refresh_token_endpoint(refresh_token: str=Body(...)):
#     try:
#         payload = decode_token(refresh_token)
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

#     if payload.get("type") != "refresh":
#         raise HTTPException(status_code=401, detail="Expected a refresh token")

#     user_id = payload.get("sub")
#     if user_id is None:
#         raise HTTPException(status_code=401, detail="Invalid token payload")

#     # Optionally: check DB that the refresh token is still allowed (not revoked).
#     # Optionally: issue a new refresh token too (refresh rotation).
#     new_access = create_access_token({"sub": str(user_id)})
#     new_refresh = create_refresh_token({"sub": str(user_id)})

#     return {
#         "access_token": new_access,
#         "refresh_token": new_refresh,
#         "token_type": "bearer",
#         "expires_in": int(ACCESS_TOKEN_EXPIRE_MINUTES * 60)
#     }

# @app.get("/tasks/{task_id}", dependencies=[Depends(bearer_scheme)])
# def get_task(request: Request, task_id: int):
#     db = SessionLocal()
#     current_user_id = request.state.user_id
#     task = db.query(models.Task).filter(models.Task.id==task_id).first()
    
#     if not task:
#         db.close()
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     if task.user_id != current_user_id:
#         db.close()
#         raise HTTPException(status_code=403, detail="Not authorized to view this task")
#     db.close()
#     return {
#         "id": task.id,
#         "user_id": task.user_id,
#         "description": task.description,
#         "status": task.status,
#         "assignee_id": task.assignee_id
        
#     }




# @app.get("/users/{user_id}/tasks")
# def list_tasks(user_id: int):
    
#     db = SessionLocal()
    
#     user = db.query(models.User).filter(models.User.id == user_id).first()
#     if not user:
#         db.close()
#         raise HTTPException(status_code=404, detail="User not found")
    
#     tasks= db.query(models.Task).filter(models.Task.user_id == user_id).all()
#     db.close()
#     return tasks


# @app.put("/tasks/{task_id}", dependencies=[Depends(bearer_scheme)])
# def update_task(request: Request, task_id: int, status: str):
#     db = SessionLocal()
#     current_user_id = request.state.user_id
    
#     task = db.query(models.Task).filter(models.Task.id==task_id).first()
    
#     if not task:
#         db.close()
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     if task.user_id != current_user_id:
#         db.close()
#         raise HTTPException(status_code=403, detail="Not authorized to update this task")
    
#     task.status=status
#     db.commit()
#     db.refresh(task)
#     db.close()
    
#     return task
    
# @app.delete("/tasks/{task_id}", dependencies=[Depends(bearer_scheme)])
# def delete_task(request: Request, task_id: int):
#     db = SessionLocal()
#     current_user_id = request.state.user_id
#     task = db.query(models.Task).filter(models.Task.id==task_id).first()
    
#     if not task:
#         db.close()
#         raise HTTPException(status_code=404, detail="Task not found")
#     if task.user_id != current_user_id:
#         db.close()
#         raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    
#     db.delete(task)
#     db.commit()
#     db.close()


# @app.post("/profile", dependencies=[Depends(bearer_scheme)])
# def create_user_profile(request:Request, first_name: str, last_name: str, profile_picture: str = None):
#     db = SessionLocal()
#     current_user_id = request.state.user_id
#     user = db.query(models.User).filter(models.User.id==current_user_id).first()
    
#     if not user:
#         db.close()
#         raise HTTPException(status_code=404, detail="User not found")
    
#     existing_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id==current_user_id).first()
    
#     if existing_profile:
#         db.close()
#         raise HTTPException(status_code=400, detail="User profile already exists")
    
#     new_profile = models.UserProfile(user_id=current_user_id, first_name=first_name, last_name=last_name, profile_picture=profile_picture)
#     db.add(new_profile)
#     db.commit()
#     db.refresh(new_profile)
#     db.close()
    
#     return {
#         "id": new_profile.id,
#         "user_id": new_profile.user_id,
#         "first_name": new_profile.first_name,
#         "last_name": new_profile.last_name,
#         "profile_picture": new_profile.profile_picture
#     }
    

import os
from fastapi import Depends, FastAPI, Body, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError

from database import SessionLocal
import models
from security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    hash_password,
    verify_password,
    decode_token,
    create_access_token,
    create_refresh_token,
)
from ai_agent import run_agent_for_user

app = FastAPI()
bearer_scheme = HTTPBearer()

EXCLUDED_PATHS = {
    "/ui",
    "/login",
    "/users",
    "/refresh",
    "/openapi.json",
    "/docs",
    "/redoc",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing token"})

    token = auth_header.split(" ")[1]
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return JSONResponse(status_code=401, content={"detail": "Invalid token type"})
        sub = payload.get("sub")
        if sub is None:
            return JSONResponse(status_code=401, content={"detail": "Invalid token payload"})
        request.state.user_id = int(sub)
    except JWTError:
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    return await call_next(request)


@app.get("/ui")
def serve_ui():
    return FileResponse(os.path.join(BASE_DIR, "client_ui.html"))


@app.post("/users")
def create_user(name: str, password: str):
    db = SessionLocal()
    try:
        new_user = models.User(name=name, password=hash_password(password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"id": new_user.id, "name": new_user.name}
    finally:
        db.close()


@app.post("/login")
def login_user(name: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.name == name).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Incorrect password")

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return {
            "message": "Login successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user.id,
            "token_type": "Bearer",
        }
    finally:
        db.close()


@app.post("/refresh")
def refresh_token_endpoint(refresh_token: str = Body(...)):
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Expected a refresh token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return {
        "access_token": create_access_token({"sub": str(user_id)}),
        "refresh_token": create_refresh_token({"sub": str(user_id)}),
        "token_type": "bearer",
        "expires_in": int(ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    }


@app.get("/me", dependencies=[Depends(bearer_scheme)])
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(payload.get("sub"))


@app.post("/tasks", dependencies=[Depends(bearer_scheme)])
def create_task(request: Request, description: str, status: str, assignee_id: int = None):
    db = SessionLocal()
    try:
        current_user_id = request.state.user_id

        user = db.query(models.User).filter(models.User.id == current_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Authenticated user not found")

        if assignee_id is not None:
            assignee = db.query(models.User).filter(models.User.id == assignee_id).first()
            if not assignee:
                raise HTTPException(status_code=404, detail="Assignee not found")

        new_task = models.Task(
            user_id=current_user_id,
            description=description,
            status=status,
            assignee_id=assignee_id,
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        return {
            "id": new_task.id,
            "user_id": new_task.user_id,
            "description": new_task.description,
            "status": new_task.status,
            "assignee_id": new_task.assignee_id,
        }
    finally:
        db.close()


@app.get("/tasks/mine", dependencies=[Depends(bearer_scheme)])
def list_my_tasks(request: Request):
    db = SessionLocal()
    try:
        current_user_id = request.state.user_id
        tasks = db.query(models.Task).filter(models.Task.user_id == current_user_id).all()
        return [
            {
                "id": t.id,
                "user_id": t.user_id,
                "description": t.description,
                "status": t.status,
                "assignee_id": t.assignee_id,
            }
            for t in tasks
        ]
    finally:
        db.close()


@app.get("/tasks/{task_id}", dependencies=[Depends(bearer_scheme)])
def get_task(request: Request, task_id: int):
    db = SessionLocal()
    try:
        current_user_id = request.state.user_id
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this task")
        return {
            "id": task.id,
            "user_id": task.user_id,
            "description": task.description,
            "status": task.status,
            "assignee_id": task.assignee_id,
        }
    finally:
        db.close()


@app.put("/tasks/{task_id}", dependencies=[Depends(bearer_scheme)])
def update_task(request: Request, task_id: int, status: str):
    db = SessionLocal()
    try:
        current_user_id = request.state.user_id
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this task")

        task.status = status
        db.commit()
        db.refresh(task)
        return {"id": task.id, "status": task.status}
    finally:
        db.close()


@app.delete("/tasks/{task_id}", dependencies=[Depends(bearer_scheme)])
def delete_task(request: Request, task_id: int):
    db = SessionLocal()
    try:
        current_user_id = request.state.user_id
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this task")

        db.delete(task)
        db.commit()
        return {"message": "Task deleted", "task_id": task_id}
    finally:
        db.close()


@app.get("/users/list")
def get_users():
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        return [{"user_id": user.id, "name": user.name} for user in users]
    finally:
        db.close()


@app.get("/users/{user_id}/tasks")
def list_tasks(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return db.query(models.Task).filter(models.Task.user_id == user_id).all()
    finally:
        db.close()


@app.post("/profile", dependencies=[Depends(bearer_scheme)])
def create_user_profile(request: Request, first_name: str, last_name: str, profile_picture: str = None):
    db = SessionLocal()
    try:
        current_user_id = request.state.user_id
        user = db.query(models.User).filter(models.User.id == current_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        existing_profile = (
            db.query(models.UserProfile).filter(models.UserProfile.user_id == current_user_id).first()
        )
        if existing_profile:
            raise HTTPException(status_code=400, detail="User profile already exists")

        new_profile = models.UserProfile(
            user_id=current_user_id,
            first_name=first_name,
            last_name=last_name,
            profile_picture=profile_picture,
        )
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        return {
            "id": new_profile.id,
            "user_id": new_profile.user_id,
            "first_name": new_profile.first_name,
            "last_name": new_profile.last_name,
            "profile_picture": new_profile.profile_picture,
        }
    finally:
        db.close()


class AgentRequest(BaseModel):
    instruction: str


@app.post("/agent/execute", dependencies=[Depends(bearer_scheme)])
async def agent_execute(payload: AgentRequest, request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    result = await run_agent_for_user(
        auth_header=auth_header,
        instruction=payload.instruction,
    )
    return {"ok": True, "user_id": request.state.user_id, "result": result}
