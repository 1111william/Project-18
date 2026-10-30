# Database migrations

The revision history is authoritative for database creation and upgrades.

- `20261004_0001` freezes the original eleven-table schema before hardening.
- `20261004_0002` adds objective integrity checks and utf8mb4 table storage.

Do not stamp an existing database until `audit_existing.py` passes and a human
has confirmed the result. See `backend/docs/database.md` for the full procedure.
