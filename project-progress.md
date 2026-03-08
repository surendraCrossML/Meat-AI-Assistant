# Meat-AI-Assistant — Project Progress

## Overview

FastAPI backend for the Meat AI Assistant application. The following tasks have been completed:

---

## ✅ TASK 1: Database Models

**Stack**: SQLAlchemy 2.0 + Alembic + PostgreSQL (NeonDB via psycopg2-binary)

### Models Created

| Model          | Table              | File                             |
| -------------- | ------------------ | -------------------------------- |
| User           | `users`            | `app/models/user.py`             |
| Document       | `documents`        | `app/models/document.py`         |
| N8nChatHistory | `n8n_chat_history` | `app/models/n8n_chat_history.py` |

### Field Details

**User**

- `id` (PK, Integer)
- `user_name` (String 100)
- `user_email` (String 255, unique, indexed)
- `user_password` (String 255, bcrypt hash)
- `user_role` (Enum: `admin` | `user`)
- `user_created_at` (DateTime, server default)
- `user_updated_at` (DateTime, auto-updated)

**Document**

- `id` (PK, Integer)
- `document_name` (String 255)
- `document_type` (String 100, MIME type)
- `document_size` (BigInteger, bytes)
- `description` (Text, nullable)
- `s3_key` (String 512, unique — S3 object path)
- `user_id` (FK → `users.id`, CASCADE DELETE)
- `document_created_at` (DateTime)
- `document_updated_at` (DateTime)

**N8nChatHistory**

- `id` (PK, Integer)
- `session_id` (String 255, indexed)
- `message` (Text — JSON string of role + content)

### Alembic Migration Commands

```bash
# 1. Initialize (already done)
alembic init alembic

# 2. Create migration scripts (run from project root with venv active)
alembic revision --autogenerate -m "create users table"
alembic revision --autogenerate -m "create documents table"
alembic revision --autogenerate -m "create n8n_chat_history table"

# 3. Apply all migrations to the database
alembic upgrade head

# 4. Other useful commands
alembic current          # Show current migration version
alembic history          # Show migration history
alembic downgrade -1     # Rollback one step
alembic downgrade base   # Rollback all migrations
```

> **Note**: `Base.metadata.create_all(bind=engine)` is called on server startup for quick bootstrapping. For production, use `alembic upgrade head` instead.

---

## ✅ TASK 2: S3 Bucket Integration

**Stack**: boto3, AWS S3 (`ap-south-1`, bucket: `ai-meat-assistant-documents-v1`)

### API Endpoints

| Method   | Path                       | Description                            |
| -------- | -------------------------- | -------------------------------------- |
| `POST`   | `/documents/upload`        | Upload file to S3, save metadata in DB |
| `GET`    | `/documents/`              | List all documents for current user    |
| `GET`    | `/documents/{id}/download` | Get presigned URL (expires in 1 hour)  |
| `DELETE` | `/documents/{id}`          | Delete from S3 + remove DB record      |

### S3 Key Format

Files are stored as: `<user_id>/<uuid>-<original_filename>`

### Files

- `app/services/s3_service.py` — boto3 helpers: upload, presigned URL, delete, list

---

## ✅ TASK 3: JWT Authentication + Swagger Protection

**Stack**: python-jose (HS256), passlib (bcrypt), FastAPI HTTPBearer

### Auth Endpoints

| Method | Path             | Description                                |
| ------ | ---------------- | ------------------------------------------ |
| `POST` | `/auth/register` | Register new user (bcrypt hashed password) |
| `POST` | `/auth/login`    | Login → returns JWT `access_token`         |

### How to Use

1. Open Swagger: `http://localhost:8000/docs`
2. **Register** → `POST /auth/register`
3. **Login** → `POST /auth/login` → copy `access_token`
4. Click **🔓 Authorize** button → enter `Bearer <token>`
5. All `/documents/*` routes are now accessible

### Files

- `app/auth/jwt.py` — `create_access_token`, `verify_token`
- `app/auth/dependencies.py` — `get_current_user` FastAPI dependency
- `app/routes/auth.py` — register + login routes
- `app/main.py` — global `BearerAuth` OpenAPI security scheme

---

## Project Structure

```
app/
├── auth/
│   ├── dependencies.py     # get_current_user dependency
│   └── jwt.py              # Token creation & verification
├── core/
│   └── config.py           # All env vars (AWS, DB, JWT)
├── db/
│   └── base.py             # SQLAlchemy engine, SessionLocal, Base
├── models/
│   ├── document.py
│   ├── n8n_chat_history.py
│   └── user.py
├── routes/
│   ├── auth.py
│   ├── documents.py
│   └── health.py
├── schemas/
│   └── schemas.py          # Pydantic request/response schemas
├── services/
│   └── s3_service.py       # AWS S3 boto3 helpers
└── main.py                 # FastAPI app + Swagger auth config
alembic/                    # Alembic migration environment
alembic.ini
requirements.txt
.env
```

---

_Generated: 2026-02-27_
