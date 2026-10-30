# Backend deployment

Railway and AWS do not require a different FastAPI framework or a fork of the application. The same image runs in both places; only runtime variables, networking, health checks, secrets, and the external MySQL location change.

## Image contract

Build from the repository root so `backend/Dockerfile` can copy the locked requirements and backend package:

```sh
docker build -f backend/Dockerfile -t project18-backend .
```

The image runs as a non-root user, logs to stdout/stderr, reads `PORT` (default `8000`), and uses an exec-style Python entry point so Uvicorn receives `SIGTERM`. Its built-in liveness check requests `/api/live`.

Startup intentionally does not seed data, create tables, or run migrations. Run `python -m alembic -c backend/alembic.ini upgrade head` as a separate one-off release task before new application code receives traffic. The hardening revision converts all application tables to `utf8mb4_unicode_ci` and adds enforced checks; because MySQL DDL auto-commits, snapshot first and rehearse the upgrade on staging. Seed/reset is only for an empty or explicitly confirmed loopback `_dev`/`_test` database and has no production override.

Do not apply the baseline migration blindly to an existing shared schema. The database owner must back it up, audit it against the frozen baseline, explicitly stamp the verified baseline revision, and only then upgrade. Ambiguous or non-matching schemas require a reviewed reconciliation migration, not `seed.py`.

## Production baseline

Set at least:

```text
APP_ENV=production
DEBUG=0
DATABASE_URL=<SQLAlchemy MySQL URL>
SESSION_SECRET=<unique random value, at least 32 characters>
ALLOWED_ORIGINS=https://the-exact-frontend-origin.example
SESSION_COOKIE_SECURE=1
SESSION_COOKIE_SAMESITE=none
DB_SSL_MODE=verify_identity
DB_SSL_CA=<mounted path to the database provider's CA bundle>
TRUSTED_PROXY_HEADERS=0
```

Use `SESSION_COOKIE_SAMESITE=lax` when frontend and API are same-site. `none` is only for a genuinely cross-site browser deployment and must be paired with HTTPS and a secure cookie. Never use `*` for credentialed CORS. Even with those settings correct, browser third-party-cookie policies can block cross-site sessions; prefer same-site hostnames or a frontend reverse proxy where practical, and verify the deployed flow in the target browsers.

`DB_SSL_MODE=required` encrypts transport but does not verify the database identity. Use `verify_ca` or preferably `verify_identity` when the provider supplies a CA bundle, and set `DB_SSL_CA` to the path actually mounted in that runtime. The example path is not a certificate and must not be copied literally; confirm the TLS requirements and CA material for the specific Railway or AWS database before production.

All replicas must use the same `SESSION_SECRET`; changing it invalidates every active session. Keep the database outside the application container on persistent MySQL storage. Mount TLS certificate files read-only when certificate verification is enabled.

Proxy headers are disabled by default. Enable `TRUSTED_PROXY_HEADERS=1` with a reviewed `FORWARDED_ALLOW_IPS` list of actual proxy IPs or networks. An explicit `*` is acceptable only when the network design guarantees the container cannot be reached except through the trusted ingress; otherwise it permits direct clients to spoof forwarding headers. Never make `*` the default merely to get a deployment working.

## Railway

For a new service, use the Railway dashboard as the source of truth. Keep the service root directory at the repository root and select `backend/Dockerfile` under Build Configuration; Railway also currently supports the `RAILWAY_DOCKERFILE_PATH` service variable for a custom path. Do not change the root to `/backend`, because that breaks this image's repository-root build context. Railway injects `PORT`, which `backend/serve.py` reads automatically.

Configure these service settings:

1. Add persistent Railway MySQL in the same project/environment, or provide another durable MySQL endpoint.
2. Inject database values with Railway reference variables. Resolution order is `DATABASE_URL`, `MYSQL_URL`, then individual fields (`DB_*` before the corresponding Railway `MYSQL*` alias). Remove or clear both URL variables if you intend field overrides to apply.
3. Set the production variables above and generate a public HTTPS domain for the API.
4. In Deploy settings, set the health path to `/api/health`, timeout to 120 seconds, and restart policy to On Failure with at most three retries. The health request verifies MySQL before Railway switches traffic; `/api/live` remains the process-only diagnostic.
5. Run `python -m alembic -c backend/alembic.ini upgrade head` as an explicit one-off operation. There is no `preDeployCommand` or seed command in this repository by design.

Railway private DNS (`*.railway.internal`) is scoped to one Railway project environment. An API running on AWS cannot connect to a Railway MySQL private hostname; use a securely exposed TLS endpoint or, preferably, move the database into an AWS VPC such as RDS.

As of October 2026, Railway marks Config as Code as legacy-only with an end date of 1 December 2026. The repository's `railway.json` is retained only as a readable legacy reference; do not rely on it being applied to a new service. Enter and verify the settings above in the dashboard, and use Railway's replacement workflow if an existing legacy service is migrated.

## AWS container options

No AWS infrastructure is created by this repository. The image can run unchanged on either ECS (Fargate or EC2 capacity) or Docker on an EC2 instance.

For ECS:

- Push the image to ECR and set container port/`PORT` to `8000`.
- Prefer `awsvpc` networking. Put tasks in private subnets and allow inbound traffic only from the load balancer security group.
- Put RDS/Aurora MySQL in the same VPC or connected network. Its security group should accept MySQL only from the task/instance security group.
- Use `/api/live` for the ECS container health command and `/api/health` for the Application Load Balancer target-group health path.
- Inject `SESSION_SECRET` and database credentials from Secrets Manager or SSM Parameter Store, not plaintext task-definition environment entries. A rotated injected secret needs a new task deployment.
- Configure the `awslogs` driver so stdout/stderr reaches CloudWatch Logs.
- Terminate public TLS at an ALB (or another reviewed ingress) and keep exact HTTPS origins in `ALLOWED_ORIGINS`.

For a single EC2 Docker host, apply the same environment and TLS rules, publish only through the HTTPS reverse proxy/load balancer, and keep MySQL off the public interface. ECS is usually easier to operate safely once replicas and rolling deployments are needed; this is an operational choice, not an application-framework change.

For RDS MySQL, `verify_identity` plus the current AWS RDS CA bundle provides encryption and hostname verification. Plan CA rotation rather than copying a certificate into source control.

## Verification after deployment

1. Confirm `/api/live` returns 200.
2. Confirm `/api/health` returns 200 and identifies the database as up.
3. Confirm an uncredentialed protected request returns the normalized `401 UNAUTHENTICATED` envelope.
4. From the real frontend origin, verify credentialed CORS and a cookie-authenticated write, including Origin/Referer protection.
5. Confirm cross-parent child access is rejected and logs do not expose secrets.
6. Confirm graceful shutdown during a rolling replacement and that all replicas share the session secret.

## Official platform references

- Railway: [Dockerfiles](https://docs.railway.com/builds/dockerfiles), [health checks and `PORT`](https://docs.railway.com/deployments/healthchecks), [private networking scope](https://docs.railway.com/networking/private-networking), and [Config as Code status](https://docs.railway.com/config-as-code/reference).
- Uvicorn: [proxy headers and allowed forwarding IPs](https://www.uvicorn.org/settings/).
- Docker: [exec-form commands and signal handling](https://docs.docker.com/reference/dockerfile/).
- AWS: [ECS networking security](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-network.html), [container health checks](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/healthcheck.html), [Secrets Manager injection](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html), [CloudWatch `awslogs`](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/specify-log-config.html), and [RDS MySQL TLS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/mysql-ssl-connections.html).
