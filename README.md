# Bangla Learning Platform — Project 18

This repository contains a Vue frontend scaffold and a FastAPI/MySQL backend foundation for a Bangla learning platform.

## Repository layout

- `backend/`: API, data model, tests, container image, and deployment guidance.
- `frontend/`: minimal Vue 3/Vite scaffold; product screens and backend integration are not implemented yet.
- `compose.yaml`: optional local-only API and MySQL environment.
- `railway.json`: legacy Railway Config-as-Code reference; configure a new service in the Railway dashboard rather than assuming this file is applied.

## Implementation status

Child-profile CRUD, account registration and password login, password recovery, parent PIN verification, and the shared response/error conventions are the current backend integration base. Complete Quiz behavior remains assigned work.

## Start here

- Backend development: [backend/README.md](backend/README.md)
- API contract: [backend/docs/api-contract.md](backend/docs/api-contract.md)
- Railway/AWS/container deployment: [backend/docs/deployment.md](backend/docs/deployment.md)
- Frontend scaffold: [frontend/README.md](frontend/README.md)

For the optional local container environment, first copy `backend/.env.example` to `backend/.env` and replace its `SESSION_SECRET` placeholder. Then follow the migration and safe-seed sequence in the backend guide, beginning with:

```sh
docker compose up -d db
```

Container startup does not run migrations or seed data. Never run the destructive seed script against a shared, staging, or production database.
