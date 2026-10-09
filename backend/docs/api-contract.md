# API contract

This document defines the shared frontend/backend conventions. Account, parent-PIN, and child-profile routes are supported; the Quiz routes remain placeholders.

## JSON envelope

Completed foundation endpoints under `/api` return JSON using one of these shapes. New modules must follow the same contract; the unfinished Quiz scaffold is the currently documented exception.

Success:

```json
{
  "success": true,
  "data": {},
  "meta": {}
}
```

`data` and `meta` are omitted when they are not needed.

Failure:

```json
{
  "success": false,
  "error": "Human-readable message",
  "code": "STABLE_MACHINE_CODE",
  "fields": ["optional.fieldName"]
}
```

Clients branch on HTTP status and `code`, not the English `error` text. Validation errors use HTTP 400, `VALIDATION_FAILED`, and list relevant input names in `fields`. Framework-generated 404 and 405 responses are normalized to this failure shape.

Current error codes are `BAD_REQUEST`, `VALIDATION_FAILED`, `UNAUTHENTICATED`, `FORBIDDEN`, `CSRF_FAILED`, `PIN_REQUIRED`, `NOT_FOUND`, `METHOD_NOT_ALLOWED`, `LIMIT_REACHED`, `INTERNAL_ERROR`, `DB_UNAVAILABLE`, and the generic `HTTP_ERROR` fallback.

## Health endpoints

| Endpoint | Meaning | Database query |
| --- | --- | --- |
| `GET /api/live` | The API process is running | No |
| `GET /api/health` | The API and MySQL dependency are available | Yes |

`/api/live` is suitable for container liveness. `/api/health` is suitable for deployment/readiness checks and external dependency monitoring.

## Sessions, authorization, and write protection

Protected routes read a signed session cookie. A missing session returns `401 UNAUTHENTICATED`; accessing another parent's child returns `403 FORBIDDEN`; a missing child returns `404 NOT_FOUND`. Admin and PIN checks are separate guards.

Unsafe cookie-authenticated methods (`POST`, `PUT`, `PATCH`, and `DELETE`) require an exact same-origin or allowed `Origin`/`Referer`; failures return `403 CSRF_FAILED`. Cross-origin browser clients must send credentials and originate from an exact entry in `ALLOWED_ORIGINS`.

Password login creates the signed session immediately; it does not require an email verification code. Registration and password recovery use short-lived email-code challenges. Parent PIN verification is a separate session flag used for parent-only areas.

## Account and parent PIN

| Method and path | Purpose |
| --- | --- |
| `POST /api/auth/register` | Request a registration email code |
| `POST /api/auth/verify-code` | Complete registration or authorize password recovery |
| `POST /api/auth/login` | Sign in directly with email and password |
| `POST /api/auth/forgot-password` | Request a password-recovery code |
| `POST /api/auth/reset-password` | Set a new password after code verification |
| `GET /api/auth/me` | Read the signed-in parent account |
| `PUT /api/auth/pin` | Set the four-digit parent PIN once |
| `POST /api/auth/pin/verify` | Verify the PIN for the current session |
| `POST /api/auth/logout` | Clear the signed session |

## Child profiles

Child-profile fields remain camelCase for compatibility.

```json
{
  "childID": 1,
  "parentID": 1,
  "nickname": "রাফি",
  "avatar": null,
  "ageBand": "junior",
  "currentLevelID": 1,
  "levelTitle": "Beginner",
  "createdAt": "2026-10-04T00:00:00"
}
```

| Method and path | Purpose | Success `data` |
| --- | --- | --- |
| `GET /api/children` | List the signed-in parent's children | Array of child summaries |
| `POST /api/children` | Create a child | `{ "childID": 4 }` |
| `GET /api/children/{childID}` | Read an owned child | Child object |
| `PUT /api/children/{childID}` | Update an owned child | `{ "childID": 4 }` |
| `POST /api/children/{childID}/delete-code` | Request the child-deletion email code | Challenge data |
| `DELETE /api/children/{childID}` | Verify the code and delete an owned child | `{ "deleted": 4 }` |

Create accepts `nickname` (1–60 characters), optional `avatar`, and `ageBand` (`junior` or `senior`). Update accepts the same fields optionally. Whitespace-only nicknames are rejected after trimming. On update, explicit `null` clears `avatar`; explicit `null` for `nickname` or `ageBand` returns HTTP 400 `VALIDATION_FAILED`.

## Quiz status

The current Quiz routes and bare response payloads are scaffolding and are not yet covered by the shared envelope. Persistence, child ownership, submission bodies, scoring, repeat-attempt rules, authorization, and envelope conversion still need team implementation and contract tests. Frontend code should not depend on the placeholder Quiz payloads yet.

## Change coordination

- Use `backend.app.config`; `backend.app.comfig` remains only as a compatibility shim and must not gain new imports.
- Use `ok()`/`failure()`/`ApiError` instead of returning bare dictionaries from `/api` routes.
- Schema changes require an Alembic migration and review by the database owner; never create or drop tables during web startup.
