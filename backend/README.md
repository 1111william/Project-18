# Backend

FastAPI and MySQL backend for the Bangla learning platform.

## Running locally

All commands are run from the repository root, not from `backend/`. The import paths are `backend.app.*`, so the working directory has to be the repository root.

```
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
python backend/scripts/seed.py
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation, which is generated from the code.

With Docker instead:

```
docker compose up --build
docker compose exec api python backend/scripts/seed.py
```

`backend/scripts/seed.py` drops every table, recreates them from the models and loads test data. It is destructive by design. Do not run it against the shared database once other members depend on the data in it.

## Response format

Every endpoint returns one of two shapes.

Success:

```json
{ "success": true, "data": {}, "meta": {} }
```

Failure:

```json
{ "success": false, "error": "Message", "code": "ERROR_CODE", "fields": ["fieldName"] }
```

Return the first with `ok()` from `backend.app.core.responses`. Produce the second by raising `ApiError` or one of its subclasses. Do not return bare dictionaries, because the frontend handles errors in one place.

## Error codes

| HTTP | Code | Meaning |
| --- | --- | --- |
| 400 | VALIDATION_FAILED | Bad input, `fields` lists the keys |
| 401 | UNAUTHENTICATED | No session |
| 403 | FORBIDDEN | Signed in but not allowed |
| 403 | PIN_REQUIRED | Child mode needs PIN verification |
| 404 | NOT_FOUND | Route or record missing |
| 409 | LIMIT_REACHED | Business rule blocked the write |
| 500 | INTERNAL_ERROR | Unhandled exception |
| 503 | DB_UNAVAILABLE | Database unreachable |

Pydantic validation errors are converted to `VALIDATION_FAILED` automatically, so declaring a schema is enough to get a correct 400.

## Adding a router

Create `backend/app/routers/yourmodule.py`, define an `APIRouter`, register it in `backend/app/main.py`.

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.responses import ok
from backend.app.database import get_db
from backend.app.models import LearningLevel

router = APIRouter()


@router.get("")
def list_levels(db: Session = Depends(get_db)):
    rows = db.scalars(select(LearningLevel).order_by(LearningLevel.levelOrder)).all()
    return ok([{"levelID": r.levelID, "title": r.title} for r in rows])
```

`backend/app/routers/children.py` is the reference implementation covering all four verbs, validation, the child limit and ownership checks.

## Guards

| Dependency | Effect |
| --- | --- |
| `Depends(current_parent_id)` | Returns parentID, raises 401 if not signed in |
| `Depends(require_admin)` | Returns parentID, raises 403 if not admin |
| `Depends(owned_child)` | Returns the ChildProfile, raises 403 if it belongs to another account |
| `Depends(require_pin)` | Raises 403 unless PIN was verified this session |

Any endpoint that reads or writes a child's data must take `child: ChildProfile = Depends(owned_child)` and use `child.childID`. Taking a raw `childID` from the path and querying with it directly lets any signed in parent read any child's records. The guard reads `childID` from the path parameter, so name the path parameter `childID`. Violations are logged.

## Session keys

Set by the auth router on login, read by the guards.

| Key | Meaning |
| --- | --- |
| `parentID` | Signed in parent |
| `isAdmin` | Admin flag |
| `pinVerified` | PIN entered this session |

Sessions are signed cookies. `SESSION_SECRET` must be a long random string in production, and changing it signs everyone out.

## Environment

| Variable | Purpose |
| --- | --- |
| `DB_HOST` `DB_PORT` `DB_NAME` `DB_USER` `DB_PASSWORD` | Database connection |
| `SESSION_SECRET` | Cookie signing key |
| `ALLOWED_ORIGINS` | Comma separated CORS whitelist |
| `CROSS_SITE_COOKIE` | `1` when the frontend is on a different domain, requires HTTPS |
| `DEBUG` | `1` returns exception detail in responses, set `0` before handover |
| `MAX_CHILDREN_PER_PARENT` | Child profile limit per account |

`backend/.env` is gitignored and must never be committed. It holds the shared database password.

## Schema

Eleven tables. Everything about a child cascades from `Parent`, so deleting an account removes its children, progress and results.

```
Parent
  └── ChildProfile ──┬── Progress ── Lesson
                     └── QuizResult ── Quiz

LearningLevel
  └── Lesson ──┬── LearningContent ── AudioResource
               ├── AudioResource
               └── Quiz ── QuizQuestion ── QuizOption
```

`AudioResource.source` is `tts` or `human` with a `verified` flag, so generated audio can be swapped for real recordings later without code changes.

`Lesson.strand` is `letters` or `culture`. `ChildProfile.ageBand` is `junior` or `senior`, which decides whether a child starts at letters or can go straight to culture.

Every table uses utf8mb4. Bangla characters are three bytes in UTF-8 and are corrupted under the default collation.

Models in `backend/app/models/entities.py` are the source of truth. Tables are created from them, so schema changes are made in Python.
