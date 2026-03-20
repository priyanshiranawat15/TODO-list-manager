# FlowList

FlowList is a multi-user task management platform with an AI assistant built in.

It combines secure authentication, personal task ownership, soft delete safety, and conversational automation so users can manage work naturally without losing data integrity.

---

## Why FlowList Is Useful

Most todo apps are either:
- Too simple (no proper auth, no access control), or
- Too complex (heavy setup, poor UX for fast task updates)

FlowList sits in the middle with practical engineering choices:
- JWT-based auth with refresh token support
- Strong per-user isolation
- Soft delete instead of destructive delete
- Agent-driven actions for natural-language task operations
- Persisted user-specific chat/session history

This makes it useful for both:
- Real usage as a starter productivity app
- Learning modern backend patterns in a clean, understandable codebase

---

## Feature Highlights

### Authentication and Session Security
- User registration and login
- Access token + refresh token flow
- Middleware-based JWT protection for private endpoints
- Duplicate username handling with proper `409 Conflict`

### Multi-User Task Management
- Create, read, update, delete task endpoints
- Ownership checks on protected resources
- Optional task assignment field (`assignee_id`)

### Soft Delete Lifecycle
- Tasks are not physically removed
- `isDeleted` marks logical deletion
- `deletedAt` captures deletion timestamp
- Standard task listing excludes soft-deleted rows

### AI Assistant Integration
- Natural-language task operations through `/agent/execute`
- Tool-based task actions (create/list/update/delete/users)
- Per-user agent response continuity via `agent_sessions`
- Persisted user/assistant messages in `messages`
- Reloadable chat history via `/agent/history`

### Built-In Frontend
- Backend-served UI at `/ui`
- Login/Register tabs with one dynamic auth submit action
- Enter-to-send and Shift+Enter multiline support in chat
- Session restore and per-user history sync

---

## Architecture Overview

- **Backend**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Security**: Passlib (bcrypt) + python-jose (JWT)
- **AI**: OpenAI Agents SDK + function tools
- **HTTP Client**: httpx
- **Environment Management**: python-dotenv
- **Frontend**: Single-page HTML/CSS/Vanilla JS

### Core Files
- `app.py`: API routes, middleware, auth flow, task/profile endpoints, agent endpoints
- `ai_agent.py`: tool-enabled agent and per-user continuity logic
- `models.py`: SQLAlchemy models (`User`, `Task`, `UserProfile`, `AgentSession`, `Message`)
- `security.py`: password hashing and JWT helper functions
- `database.py`: engine/session configuration
- `client_ui.html`: browser UI
- `alembic/versions/`: migration history

---

## Data Model Snapshot

### `users`
- `id`, `name` (unique), `password` (hashed)
- `create_at`, `update_at`

### `tasks`
- `id`, `user_id`, `description`, `status`, `assignee_id`
- `isDeleted`, `deletedAt`
- `create_at`, `update_at`

### `user_profiles`
- one profile per user
- `first_name`, `last_name`, optional `profile_picture`

### `agent_sessions`
- one session row per user
- stores `last_response_id` for agent continuity

### `messages`
- stores user and assistant messages per user
- enables chat history restore

---

## API Quick Map

### Public
- `POST /users`
- `POST /login`
- `POST /refresh`
- `GET /ui`
- `GET /docs`
- `GET /redoc`

### Protected (Bearer token required)
- `GET /me`
- `POST /tasks`
- `GET /tasks/mine`
- `GET /tasks/{task_id}`
- `PUT /tasks/{task_id}`
- `DELETE /tasks/{task_id}`
- `GET /users/list`
- `GET /users/{user_id}/tasks`
- `POST /profile`
- `POST /agent/execute`
- `GET /agent/history`

---

## Local Setup

## 1) Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

## 2) Install dependencies
Install all packages used by this project (example):
```bash
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary passlib[bcrypt] python-jose python-dotenv httpx openai agents
```

## 3) Configure PostgreSQL
Default connection currently expects:
- `postgresql://postgres:postgres@localhost:5432/todolist`

Create database:
```sql
CREATE DATABASE todolist;
```

If needed, update:
- `database.py`
- `alembic.ini`

## 4) Create environment file
```bash
cp .env.example .env
```

Set values in `.env`:
```env
JWT_SECRET_KEY=replace_with_a_long_random_secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.1
APP_BASE_URL=http://127.0.0.1:8000
```

## 5) Run migrations
```bash
alembic upgrade head
```

## 6) Start application
```bash
uvicorn app:app --reload
```

## 7) Open app
- UI: `http://127.0.0.1:8000/ui`
- API docs: `http://127.0.0.1:8000/docs`

---

## Usage Flow

1. Register a new account
2. Login and receive access/refresh tokens
3. Create tasks from UI or API
4. Use assistant prompts like:
   - `List my pending tasks`
   - `Create task: submit weekly report, status pending`
   - `Mark task 3 as done`
5. Soft delete tasks when needed
6. Logout/login and verify history restores per user

---

## Testing Checklist

### Auth
- Register new username succeeds
- Register duplicate username returns `409`
- Wrong login password returns `401`
- Protected route without token returns `401`

### Authorization
- User sees only own tasks
- Cross-user task read/update/delete is blocked

### Soft Delete
- Delete marks task as deleted (`isDeleted=true`)
- `deletedAt` is set
- Deleted task no longer appears in active listings

### Agent
- Without `OPENAI_API_KEY`, `/agent/execute` returns clear `503`
- With key configured, assistant responds and task actions execute
- `/agent/history` returns only current user's messages

### UI
- Login/Register tabs switch correctly
- Single auth submit button behaves by mode
- Chat input clears after send
- Enter sends message; Shift+Enter inserts newline

---

## Security Notes

- Never commit `.env`
- Rotate API keys immediately if exposed anywhere
- Use a strong random JWT secret in real environments
- Consider rate limiting and audit logging for production hardening

---

## Migration Notes

Recent migration path includes:
- Agent session/message tables
- Task soft delete columns
- Follow-up migration to enforce `isDeleted` non-null with default `false`

Always run:
```bash
alembic upgrade head
```

before launching latest code.

---

## Future Improvements

- Add `requirements.txt` or `pyproject.toml` for reproducible dependency setup
- Add automated test suite (pytest + API integration tests)
- Add admin role and scoped management endpoints
- Add pagination for large task/message lists
- Add CI pipeline for linting, migrations, and tests

---

FlowList is designed to stay practical: secure enough for real workflows, simple enough to build on quickly.
