# Project 18 backend

FastAPI, SQLAlchemy, and MySQL backend for the Bangla learning platform. Run all commands from the repository root because imports use the `backend.app.*` package path.

## Current scope

The child-profile foundation, account/password session flow, parent PIN workflow, and shared API envelope are the stable integration surface. Complete Quiz persistence and business rules are still team work in progress.

See [docs/api-contract.md](docs/api-contract.md) before adding frontend calls and [docs/deployment.md](docs/deployment.md) before configuring Railway or AWS.

## Local Python setup

Python 3.12 and MySQL 8.0 are the supported baseline.

```powershell
python -m venv backend/.venv
& backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
```

On macOS/Linux, activate `backend/.venv` or call `backend/.venv/bin/python` instead. Before starting the API, replace every placeholder in `backend/.env`; generate `SESSION_SECRET` with:

```powershell
& backend/.venv/Scripts/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put that generated value in `backend/.env`, then start the development server:

```powershell
& backend/.venv/Scripts/python -m uvicorn backend.app.main:app --reload
```

The application exposes:

- `GET /api/live`: process liveness; does not query MySQL.
- `GET /api/health`: dependency health; returns `503 DB_UNAVAILABLE` when MySQL cannot be reached.
- `GET /docs`: generated OpenAPI UI in environments where it is enabled.

## Local containers

`compose.yaml` is a developer convenience, not production infrastructure. It binds both published ports to loopback: API `8000` and MySQL `3307`. Copy `backend/.env.example` to `backend/.env` first, generate a fresh `SESSION_SECRET`, keep `APP_ENV=development`, and set `DB_HOST=127.0.0.1`, `DB_PORT=3307`, and `DB_NAME=coseat18_dev`. Compose loads the secret from that file but overrides the API container's database host to the service name `db`.

```powershell
docker compose up -d db
```

The database starts empty. Migration and seed safety rules require the operator to connect from the host through `127.0.0.1:3307`; seeding from the API container is intentionally unsupported. Apply migrations from the host, then load demo data:

```powershell
& backend/.venv/Scripts/python -m alembic -c backend/alembic.ini upgrade head
& backend/.venv/Scripts/python backend/scripts/seed.py
docker compose up --build -d api
```

The default seed command is non-destructive: it requires an Alembic-head, empty database. For an intentional reset of this disposable local database only, use all three confirmation arguments:

```powershell
& backend/.venv/Scripts/python backend/scripts/seed.py --reset --confirm-database coseat18_dev --yes-really-reset
```

The reset drops only the eleven managed tables plus `alembic_version`, upgrades to head on the same connection, then inserts demo data. It is allowed only in `development`/`test`, on `localhost`, `127.0.0.1`, or `::1`, and when the resolved database name contains `_dev`, `-dev`, `_test`, or `-test`. `DATABASE_URL` is resolved before this gate, so it cannot bypass the checks. There is no override variable. Never seed or reset a shared, staging, or production database.

Stop services with `docker compose down`. Add `--volumes` only when you intentionally want to erase the local MySQL volume.

## Tests

The default test command runs offline/unit contract tests and skips the opt-in real-MySQL HTTP suite:

```powershell
& backend/.venv/Scripts/python -m unittest discover -s backend/tests -t . -v
```

For the real integration suite, first create a disposable loopback MySQL 8.0 database named `coseat18_test`. The test guard refuses non-test environments, non-loopback hosts, and names that do not end in `_test`. This PowerShell example intentionally clears complete URL variables so the shown `DB_*` values take effect:

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:MYSQL_URL -ErrorAction SilentlyContinue
$env:APP_ENV = "test"
$env:DEBUG = "0"
$env:SESSION_SECRET = & backend/.venv/Scripts/python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:ALLOWED_ORIGINS = "http://localhost:5173"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "3306"
$env:DB_USER = "root"
$env:DB_PASSWORD = "replace-for-your-disposable-mysql"
$env:DB_NAME = "coseat18_test"
$env:DB_SSL_MODE = "disabled"
$env:RUN_MYSQL_TESTS = "1"
& backend/.venv/Scripts/python -m alembic -c backend/alembic.ini upgrade head
& backend/.venv/Scripts/python -m unittest discover -s backend/tests -t . -v
```

`RUN_MYSQL_TESTS=1` is required; without it, discovery reports the real MySQL/HTTP cases as skipped. Never point this suite at shared or user-data databases.

CI applies the migrations, runs `alembic check` for model/migration drift, and runs the opted-in MySQL integration checks against a disposable MySQL 8.0 test database. It separately builds the production image and requests `/api/live`; that container smoke proves image startup, not database connectivity.

## Schema invariants

Alembic is the production schema authority. The hardening migration requires MySQL 8.0.16+ (or MariaDB 10.2.1+) so `CHECK` constraints are enforced, converts all eleven tables to `utf8mb4_unicode_ci`, and rejects existing rows that violate numeric ranges before issuing DDL. The ORM models mirror these checks for newly created disposable schemas.

MySQL DDL auto-commits, so take a database snapshot and test upgrades on staging before production. The migration deliberately does not rewrite invalid user data, and its downgrade does not reverse the Unicode conversion because doing so could be lossy.

## Configuration

Environment variables take precedence over `backend/.env`. Production platforms should inject values rather than ship an env file.

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | `development`, `test`, `staging`, or `production` |
| `DATABASE_URL`, `MYSQL_URL` | Complete SQLAlchemy MySQL URLs, checked in that order |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Explicit database settings when both URL variables are absent |
| `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE` | Railway-compatible field fallbacks after the matching `DB_*` field |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE`, `DB_CONNECT_TIMEOUT` | SQLAlchemy pool and connection limits |
| `DB_SSL_MODE` | `disabled`, `required`, `verify_ca`, or `verify_identity` |
| `DB_SSL_CA`, `DB_SSL_CERT`, `DB_SSL_KEY` | Optional TLS file paths |
| `SESSION_SECRET` | Unique random value of at least 32 characters; identical on every replica |
| `SESSION_COOKIE_NAME`, `SESSION_MAX_AGE` | Cookie name and lifetime in seconds |
| `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE` | Explicit cookie transport policy |
| `ALLOWED_ORIGINS` | Comma-separated exact HTTP(S) frontend origins |
| `DEBUG` | Must be `0` in staging and production |
| `MAX_CHILDREN_PER_PARENT` | Child profile limit |
| `PORT`, `WEB_CONCURRENCY`, `LOG_LEVEL` | Container server settings |
| `TRUSTED_PROXY_HEADERS`, `FORWARDED_ALLOW_IPS` | Opt-in proxy-header trust; disabled by default |

`CROSS_SITE_COOKIE=1` remains a compatibility shortcut, but the explicit cookie variables are preferred. Cross-site cookies require HTTPS, `SESSION_COOKIE_SECURE=1`, `SESSION_COOKIE_SAMESITE=none`, precise CORS origins, and credentialed browser requests. Browser third-party-cookie policies may still block them, so prefer a same-site deployment and test with real target browsers.

Database configuration priority is `DATABASE_URL`, then `MYSQL_URL`, then individual fields. If either complete URL is set, individual database fields are intentionally ignored; remove or clear both URL variables before using field-by-field configuration.

`DB_SSL_MODE=required` encrypts without verifying database identity. Use the provider's real CA material with `verify_ca` or `verify_identity`; do not copy an example CA path into production without mounting that file.

Proxy headers remain disabled unless explicitly enabled. Prefer concrete proxy IPs/CIDRs in `FORWARDED_ALLOW_IPS`; use `*` only when network controls make direct access to the container impossible, and never as a default.

## Integration rules

- Use `ok()` and `ApiError`; completed foundation endpoints use the shared envelope, and new modules must do the same. Quiz remains explicitly unfinished.
- Keep existing child-profile JSON names in camelCase (`childID`, `parentID`, `ageBand`, `currentLevelID`).
- Child-owned endpoints must use `Depends(owned_child)` with a path parameter named `childID`.
- Cookie-authenticated writes are protected by Origin/Referer validation; do not bypass it for new routes.
- `backend/app/config.py` is canonical. The misspelled `backend/app/comfig.py` remains only as a compatibility shim; do not add new imports from it.
- Do not add schema creation, migrations, or seed execution to the web startup path.
