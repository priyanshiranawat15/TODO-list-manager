    
import os
from fastapi import Depends, FastAPI, Body, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from openai import OpenAIError
from database import SessionLocal
import models
from datetime import datetime
from security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    hash_password,
    verify_password,
    decode_token,
    create_access_token,
    create_refresh_token,
)
from ai_agent import run_agent_for_session

load_dotenv()

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
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
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
        existing_user = db.query(models.User).filter(models.User.name == name).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="Username already exists")

        new_user = models.User(name=name, password=hash_password(password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"id": new_user.id, "name": new_user.name}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already exists")
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
        tasks = db.query(models.Task).filter(
            models.Task.user_id == current_user_id,
            models.Task.isDeleted.isnot(True),
        ).all()
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
        task = db.query(models.Task).filter(
            models.Task.id == task_id,
            models.Task.isDeleted.isnot(True),
        ).first()
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
        task = db.query(models.Task).filter(
            models.Task.id == task_id,
            models.Task.isDeleted.isnot(True),
        ).first()
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
        task = db.query(models.Task).filter(
            models.Task.id == task_id,
            models.Task.isDeleted.isnot(True),
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this task")

        task.isDeleted = True
        task.deletedAt = datetime.utcnow()
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


@app.get("/users/{user_id}/tasks", dependencies=[Depends(bearer_scheme)])
def list_tasks(request: Request, user_id: int):
    db = SessionLocal()
    try:
        current_user_id = request.state.user_id
        if current_user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view these tasks")

        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return db.query(models.Task).filter(
            models.Task.user_id == user_id,
            models.Task.isDeleted.isnot(True),
        ).all()
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
    session_id: int | None = None


@app.post("/agent/sessions", dependencies=[Depends(bearer_scheme)])
def create_agent_session(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.state.user_id

    existing_session = (
        db.query(models.AgentSession)
        .filter(
            models.AgentSession.user_id == user_id,
            ~models.AgentSession.messages.any(),
        )
        .order_by(models.AgentSession.created_at.desc(), models.AgentSession.id.desc())
        .first()
    )

    if existing_session:
        return {
            "id": existing_session.id,
            "message": "Empty session already exists. Use this session.",
            "created_at": existing_session.created_at.isoformat() if existing_session.created_at else None,
            "updated_at": existing_session.updated_at.isoformat() if existing_session.updated_at else None,
        }

    new_session = models.AgentSession(user_id=user_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "id": new_session.id,
        "created_at": new_session.created_at.isoformat() if new_session.created_at else None,
        "updated_at": new_session.updated_at.isoformat() if new_session.updated_at else None,
    }


@app.get("/agent/sessions", dependencies=[Depends(bearer_scheme)])
def list_agent_sessions(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.state.user_id
    sessions = (
        db.query(models.AgentSession)
        .filter(models.AgentSession.user_id == user_id)
        .order_by(models.AgentSession.created_at.desc())
        .all()
    )

    return [
        {
            "id": session.id,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "last_response_id": session.last_response_id,
        }
        for session in sessions
    ]


@app.get("/agent/history", dependencies=[Depends(bearer_scheme)])
def agent_history(
    request: Request,
    session_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    user_id = request.state.user_id
    bounded_limit = max(1, min(limit, 200))

    session = (
        db.query(models.AgentSession)
        .filter(
            models.AgentSession.id == session_id,
            models.AgentSession.user_id == user_id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    rows = (
        db.query(models.Message)
        .filter(models.Message.session_id == session_id)
        .order_by(models.Message.created_at.desc())
        .limit(bounded_limit)
        .all()
    )

    rows.reverse()
    return [
        {
            "role": row.role,
            "content": row.content,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@app.post("/agent/execute", dependencies=[Depends(bearer_scheme)])
async def agent_execute(
    payload: AgentRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    auth_header = request.headers.get("Authorization")

    user_id = request.state.user_id
    created_new_session = False

    if payload.session_id is None:
        session = models.AgentSession(user_id=user_id)
        db.add(session)
        db.flush()
        session_id = session.id
        created_new_session = True
    else:
        session = (
            db.query(models.AgentSession)
            .filter(
                models.AgentSession.id == payload.session_id,
                models.AgentSession.user_id == user_id,
            )
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id = session.id

    try:
        result = await run_agent_for_session(
            session_id=session_id,
            user_id=user_id,
            auth_header=auth_header,
            instruction=payload.instruction,
            db=db
        )
    except OpenAIError:
        raise HTTPException(
            status_code=503,
            detail="Agent is not configured. Set OPENAI_API_KEY and restart the server.",
        )

    assistant_text = str(result) if result is not None else ""
    db.add_all(
        [
            models.Message(session_id=session_id, role="user", content=payload.instruction),
            models.Message(session_id=session_id, role="assistant", content=assistant_text),
        ]
    )
    db.commit()

    return {
        "ok": True,
        "user_id": user_id,
        "session_id": session_id,
        "created_new_session": created_new_session,
        "result": assistant_text,
    }