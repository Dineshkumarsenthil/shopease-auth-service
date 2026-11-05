# ShopEase Authentication Service

Independent FastAPI microservice for user registration, login, password hashing and JWT authentication.
Runs in its own Docker container with its own MySQL 8 database (`shopease_auth_db`).

## Technology stack
Python 3.11, FastAPI, SQLAlchemy, Alembic, MySQL 8, Passlib/bcrypt, PyJWT, Pydantic, Docker, Docker Compose.

## Folder structure
```
shopease-auth-service/
├── app/
│   ├── main.py                  # creates app, registers router, health check
│   ├── routers/auth_routes.py   # HTTP endpoints only
│   ├── services/auth_service.py # business logic + DB operations
│   ├── models/user_model.py     # SQLAlchemy users table
│   ├── schemas/auth_schema.py   # Pydantic request/response + password rules
│   ├── core/config.py           # settings from environment variables
│   ├── core/security.py         # bcrypt hashing, JWT, auth dependencies
│   └── database/connection.py   # engine, session, get_db dependency
├── alembic/                     # migrations (versions/0001_create_users_table.py)
├── alembic.ini
├── tests/test_auth.py           # automated tests (14 scenarios + verify-token)
├── postman/                     # Postman collection
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example                 # copy to .env (never commit .env)
├── .dockerignore  .gitignore
└── README.md
```

## Database
Database `shopease_auth_db`, table `users`: id, full_name, email (unique), password_hash, role (default `user`),
is_active, created_at, updated_at. Passwords are stored only as bcrypt hashes.

## Environment setup
```
copy .env.example .env      # Windows   (cp on Linux/Mac)
```
Edit `.env`: set MySQL passwords and a long random `JWT_SECRET_KEY`
(`python -c "import secrets; print(secrets.token_hex(32))"`). Do not commit `.env`.

## Run with Docker Compose
```
docker compose up -d --build
docker compose ps
docker compose logs auth-service
```
Swagger UI: http://localhost:8001/docs  (MySQL is published on host port 3307).
Stop: `docker compose down` (add `-v` to also delete the database volume).

## Alembic migrations
Migrations run automatically when the container starts (`alembic upgrade head`). Manual commands:
```
docker compose exec auth-service alembic upgrade head
docker compose exec auth-service alembic current
docker compose exec auth-service alembic downgrade -1
```

## API endpoints
| Method | Endpoint | Auth | Purpose | Success | Errors |
|---|---|---|---|---|---|
| POST | /api/auth/register | No | Register user | 201 | 409 duplicate email, 422 validation |
| POST | /api/auth/login | No | Get JWT | 200 | 401 bad credentials, 403 inactive |
| GET | /api/auth/me | Bearer | Current user profile | 200 | 401 missing/invalid/expired token |
| POST | /api/auth/verify-token | No | Validate a token | 200 | 401 invalid/expired |
| POST | /api/auth/change-password | Bearer | Change password | 200 | 400 wrong current, 422 weak/mismatch, 401 |

Password rules: min 8 chars, upper, lower, digit, special character.

## JWT authentication
1. `POST /api/auth/login` returns `access_token`.
2. Send `Authorization: Bearer <access_token>` on protected requests (Swagger: Authorize button).
3. Token claims: `sub` (user id), `role`, `iat`, `exp`. Signed with `JWT_SECRET_KEY` / `JWT_ALGORITHM`; lifetime `ACCESS_TOKEN_EXPIRE_MINUTES`.
4. Other services can reuse `get_current_user` / `get_token_payload` from `app/core/security.py`.

## API testing
- Automated: `pip install -r requirements.txt` then `pytest -q` (SQLite in memory) → 15 tests pass.
- Swagger UI and Postman: import `postman/ShopEase_Auth_Service.postman_collection.json`.

| # | Scenario | Expected | Result |
|---|---|---|---|
| 1 | Register new user | 201 | Pass |
| 2 | Duplicate email | 409 | Pass |
| 3 | Invalid email | 422 | Pass |
| 4 | Mismatched passwords | 422 | Pass |
| 5 | Login valid | 200 | Pass |
| 6 | Login wrong password | 401 | Pass |
| 7 | Login inactive account | 403 | Pass |
| 8 | /me valid token | 200 | Pass |
| 9 | Protected, no token | 401 | Pass |
| 10 | Protected, invalid token | 401 | Pass |
| 11 | Protected, expired token | 401 | Pass |
| 12 | Change password correct | 200 | Pass |
| 13 | Change password wrong current | 400 | Pass |
| 14 | Login with new password | 200 (old → 401) | Pass |

(Replace the Result column with your own Swagger/Postman screenshots when you submit.)
