# Database lifecycle and safety

This project has one SQLAlchemy model set and one Alembic history for the eleven
shared tables. Application startup never creates, stamps, or upgrades tables.
All migration and seed commands are deliberate operator actions.

## Supported database

- MySQL 8.0.16 or newer, or MariaDB 10.2.1 or newer. Earlier releases do not
  reliably enforce `CHECK` constraints and the hardening revision refuses them.
- Every managed table uses `utf8mb4` with `utf8mb4_unicode_ci`.
- The model keeps the original CamelCase table and column names. A Windows MySQL
  server with `lower_case_table_names=1` may reflect lowercase physical table
  names; the read-only audit accepts that mode without changing production DDL.
  Alembic `check` and `revision --autogenerate` are deliberately blocked on
  such a server because Alembic otherwise reports destructive case-only table
  drops and creates. Use `audit_existing.py`; run `alembic check` only against
  case-sensitive MySQL (`lower_case_table_names=0`), such as Linux CI.

The hardening checks cover only objectively invalid values:

- level and quiz pass marks: 0 through 100;
- progress percentage: 0 through 100, and time spent: zero or greater;
- quiz-result score: 0 through 100; counts cannot be negative, total count is
  positive, correct count cannot exceed total, and attempt number is positive;
- persisted ordering fields are positive and estimated minutes are nonnegative.

They intentionally do not add disputed feature rules such as allowed lesson
strands, age bands, score rounding, or whether completion implies exactly 100%.

## Revision history

- `20261004_0001` is the frozen original eleven-table baseline. It contains no
  new hardening checks or explicit table charset.
- `20261004_0002` audits existing rows, converts the managed tables to
  `utf8mb4_unicode_ci`, and adds stable named checks.

Run commands from the repository root:

```text
python -m alembic -c backend/alembic.ini current
python -m alembic -c backend/alembic.ini history
```

Credentials come only from the backend environment settings. Do not place a
password in `backend/alembic.ini` or a command line recorded by shell history.

## Fresh, empty database

Point the environment at a newly created database, then run:

```text
python -m alembic -c backend/alembic.ini upgrade head
python backend/migrations/audit_existing.py
```

The first command executes the baseline followed by hardening. The audit should
report revision `20261004_0002`, all checks, and utf8mb4 storage.

Local demo data is optional and must come after `upgrade head`:

```text
python backend/scripts/seed.py
```

The default seed command never drops or creates tables. It refuses a database
that is not at Alembic head or whose managed tables contain any rows.

## Adopt an existing unversioned database without losing data

Do not run `stamp` merely because the eleven table names appear to exist. The
baseline asserts their full column, nullability, primary-key, foreign-key,
unique-key, and index contract.

1. Schedule a change freeze and obtain approval from every feature owner that
   writes the shared models.
2. Take and verify a restorable backup. Include schema, data, triggers, and
   routines according to the team's MySQL operations standard. Record row
   counts for all eleven managed tables.
3. Point the environment at the intended database and run the read-only audit:

   ```text
   python backend/migrations/audit_existing.py --require-unversioned
   ```

4. Stop on any `ERROR`. The tool never cleans data. Schema differences or
   invalid rows must be reviewed and corrected by the owning feature team.
   Extra unmanaged tables are warnings and require explicit team confirmation.
5. Only after `AUDIT PASS`, backup verification, and human confirmation, record
   that the existing schema corresponds to the frozen baseline:

   ```text
   python -m alembic -c backend/alembic.ini stamp 20261004_0001
   ```

6. In a maintenance window, apply hardening:

   ```text
   python -m alembic -c backend/alembic.ini upgrade head
   python backend/migrations/audit_existing.py
   python -m alembic -c backend/alembic.ini current
   ```

7. Compare row counts with the pre-migration record and run API integration
   tests before reopening writes.

Never stamp an empty or mismatched database to bypass migrations. Never run the
seed command against an existing shared database.

## MySQL DDL is not transactionally reversible

MySQL implicitly commits most `ALTER TABLE` operations. A later failure cannot
roll back earlier table conversions or constraints, even if Alembic logs a
transaction. Revision `0002` therefore validates all row predicates and any
same-named existing constraints before its first DDL statement. It also checks
that parent emails remain unique under `utf8mb4_unicode_ci`, so a case/accent
collision cannot fail after earlier table conversions have committed.

If infrastructure fails after some DDL has committed:

1. stop writes and do not change the Alembic version manually;
2. inspect `SHOW CREATE TABLE` for every affected table and compare the named
   constraints with this revision;
3. restore the verified backup, or obtain a reviewed recovery plan;
4. a retry may skip only an already-present constraint whose reflected
   definition is equivalent; the migration aborts on a same-named but different
   constraint.

Downgrading `0002` removes its named checks but deliberately does not convert
Unicode storage back to an unknown prior charset, because that could lose data.
Restore a backup if the charset conversion itself must be undone.

## Seed safety contract

The seed CLI uses the final database URL parsed by `Settings`. Resolution order
is `DATABASE_URL`, `MYSQL_URL`, then individual fields (`DB_*` before matching
`MYSQL*` aliases), so setting a harmless `DB_HOST` cannot override either remote
complete URL. Every seed mode requires:

- `APP_ENV=development` or `APP_ENV=test`;
- parsed host exactly `localhost`, `127.0.0.1`, or `::1`;
- parsed database name containing a separate `dev` or `test` marker, such as
  `coseat18_dev` or `coseat18-test`.

There is no remote-host override. A Compose service hostname such as `db` is not
accepted. For Compose, publish MySQL only on `127.0.0.1`, use a development-named
database, and run migration/seed from the host against that published port.

Set `DEMO_PARENT_PASSWORD` to control the local demo password; it must be at
least 12 characters and at most 72 UTF-8 bytes. It is validated and hashed
before reset performs any DDL. The fallback is local-only and must never be
treated as a real credential.

Destructive reset requires both confirmations in addition to all gates:

```text
python backend/scripts/seed.py --reset --confirm-database coseat18_dev --yes-really-reset
```

Reset drops only the eleven managed tables plus `alembic_version` in dependency
order, leaves foreign-key checks enabled, upgrades the same local connection to
head, and then inserts the demo rows. It does not call `create_all`. Reset also
refuses to start if an unmanaged table has a foreign key into a managed table,
which prevents a partially committed MySQL drop sequence.

## Two validation rounds

Round 1 is fully isolated and does not connect to MySQL:

```text
python -m unittest discover -s backend/tests -p "test_db_*.py" -v
python -m alembic -c backend/alembic.ini upgrade head --sql
```

The tests verify model metadata, frozen baseline SQL, hardening SQL, audit
case-folding/TLS behavior, the no-drop default, reset gates, rollback behavior,
and the internally consistent demo dataset.

Round 2 uses disposable MySQL databases only:

1. New-database path: `upgrade head`, audit, optional default seed, then verify
   row counts and rejected invalid inserts.
2. Existing-database path: load the pre-migration schema and representative
   valid rows into a separate temporary database, run `audit --require-unversioned`,
   manually stamp `0001`, upgrade to head, audit again, and compare every row
   count.

Do not use Railway, a shared integration database, or a copy that contains user
data for either validation round.
