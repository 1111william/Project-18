import os
from pathlib import Path
import re
from typing import Mapping
from urllib.parse import urlsplit

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url


BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"
COOKIE_NAME_PATTERN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")

# Platform environment variables win. Only the backend's own .env is loaded;
# the process working directory cannot silently select a different file.
load_dotenv(dotenv_path=ENV_FILE, override=False)


def _parse_bool(value: str, name: str) -> bool:
    normalised = value.strip().lower()
    if normalised in {"1", "true", "yes", "on"}:
        return True
    if normalised in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be one of 1/0, true/false, yes/no, on/off")


def _parse_int(value: str, name: str, minimum: int, maximum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if parsed < minimum or (maximum is not None and parsed > maximum):
        range_text = f"{minimum}..{maximum}" if maximum is not None else f">= {minimum}"
        raise RuntimeError(f"{name} must be in the range {range_text}")
    return parsed


def normalise_origin(value: str) -> str:
    """Validate and canonicalise an exact HTTP(S) origin."""

    candidate = value.strip()
    if not candidate or candidate == "*":
        raise RuntimeError("CORS origins must be explicit HTTP(S) origins, not empty or '*'")
    try:
        parsed = urlsplit(candidate)
    except ValueError as exc:
        raise RuntimeError(f"Invalid origin {candidate!r}") from exc
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or "*" in candidate
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise RuntimeError(f"Invalid origin {candidate!r}; use scheme://host[:port] only")
    try:
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError(f"Invalid port in origin {candidate!r}") from exc

    host = parsed.hostname.lower()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    default_port = 80 if parsed.scheme.lower() == "http" else 443
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{parsed.scheme.lower()}://{host}{port_suffix}"


class Settings:
    VALID_ENVIRONMENTS = {"development", "test", "staging", "production"}
    VALID_SSL_MODES = {"disabled", "required", "verify_ca", "verify_identity"}
    VALID_SAME_SITE = {"lax", "strict", "none"}

    def __init__(self, environ: Mapping[str, str] | None = None):
        env = os.environ if environ is None else environ
        self._environ = env

        self.APP_ENV = self._first_nonempty(env, "APP_ENV", default="development").lower()
        if self.APP_ENV not in self.VALID_ENVIRONMENTS:
            choices = ", ".join(sorted(self.VALID_ENVIRONMENTS))
            raise RuntimeError(f"APP_ENV must be one of: {choices}")

        self.DEBUG = _parse_bool(self._value(env, "DEBUG", "0"), "DEBUG")
        self.SESSION_SECRET = self._value(env, "SESSION_SECRET", "")
        self.FRONTEND_URL = self._value(env, "FRONTEND_URL", "http://localhost:5173")

        origins_raw = self._value(env, "ALLOWED_ORIGINS", self.FRONTEND_URL)
        self._allowed_origins_explicit = bool(env.get("ALLOWED_ORIGINS", "").strip())
        self.allowed_origins = self._parse_origins(origins_raw)

        self.CROSS_SITE_COOKIE = self._value(env, "CROSS_SITE_COOKIE", "0")
        cross_site = _parse_bool(self.CROSS_SITE_COOKIE, "CROSS_SITE_COOKIE")
        same_site_default = "none" if cross_site else "lax"
        self.SESSION_COOKIE_SAMESITE = self._value(
            env, "SESSION_COOKIE_SAMESITE", same_site_default
        ).strip().lower()
        if self.SESSION_COOKIE_SAMESITE not in self.VALID_SAME_SITE:
            choices = ", ".join(sorted(self.VALID_SAME_SITE))
            raise RuntimeError(f"SESSION_COOKIE_SAMESITE must be one of: {choices}")

        secure_default = self.APP_ENV in {"staging", "production"} or (
            self.SESSION_COOKIE_SAMESITE == "none"
        )
        secure_raw = env.get("SESSION_COOKIE_SECURE")
        self.SESSION_COOKIE_SECURE = (
            secure_default
            if secure_raw is None or not secure_raw.strip()
            else _parse_bool(secure_raw, "SESSION_COOKIE_SECURE")
        )
        self.SESSION_COOKIE_NAME = self._value(env, "SESSION_COOKIE_NAME", "session").strip()
        if not COOKIE_NAME_PATTERN.fullmatch(self.SESSION_COOKIE_NAME):
            raise RuntimeError("SESSION_COOKIE_NAME contains invalid cookie-name characters")
        self.SESSION_MAX_AGE = _parse_int(
            self._value(env, "SESSION_MAX_AGE", "86400"),
            "SESSION_MAX_AGE",
            1,
        )

        self.MAX_CHILDREN_PER_PARENT = _parse_int(
            self._value(env, "MAX_CHILDREN_PER_PARENT", "5"),
            "MAX_CHILDREN_PER_PARENT",
            1,
        )

        self.EMAIL_DELIVERY = self._value(
            env, "EMAIL_DELIVERY", "development"
        ).strip().lower()
        if self.EMAIL_DELIVERY not in {"development", "smtp"}:
            raise RuntimeError("EMAIL_DELIVERY must be development or smtp")
        self.AUTH_DEVELOPMENT_CODES = _parse_bool(
            self._value(env, "AUTH_DEVELOPMENT_CODES", "1"),
            "AUTH_DEVELOPMENT_CODES",
        )
        self.SMTP_HOST = self._value(env, "SMTP_HOST", "smtp.gmail.com").strip()
        self.SMTP_PORT = _parse_int(
            self._value(env, "SMTP_PORT", "587"), "SMTP_PORT", 1, 65535
        )
        self.SMTP_USERNAME = self._value(env, "SMTP_USERNAME", "").strip()
        self.SMTP_PASSWORD = self._value(env, "SMTP_PASSWORD", "").replace(" ", "")
        self.SMTP_FROM_EMAIL = self._value(env, "SMTP_FROM_EMAIL", "").strip()
        self.SMTP_FROM_NAME = self._value(env, "SMTP_FROM_NAME", "Project 18").strip()
        self.SMTP_STARTTLS = _parse_bool(
            self._value(env, "SMTP_STARTTLS", "1"), "SMTP_STARTTLS"
        )
        self.SMTP_TIMEOUT_SECONDS = _parse_int(
            self._value(env, "SMTP_TIMEOUT_SECONDS", "20"),
            "SMTP_TIMEOUT_SECONDS",
            1,
            120,
        )

        self.DB_POOL_SIZE = _parse_int(
            self._value(env, "DB_POOL_SIZE", "5"), "DB_POOL_SIZE", 1
        )
        self.DB_MAX_OVERFLOW = _parse_int(
            self._value(env, "DB_MAX_OVERFLOW", "10"), "DB_MAX_OVERFLOW", 0
        )
        self.DB_POOL_RECYCLE = _parse_int(
            self._value(env, "DB_POOL_RECYCLE", "280"), "DB_POOL_RECYCLE", 1
        )
        self.DB_CONNECT_TIMEOUT = _parse_int(
            self._value(env, "DB_CONNECT_TIMEOUT", "10"),
            "DB_CONNECT_TIMEOUT",
            1,
            120,
        )

        self._database_url = self._build_database_url(env)
        self.DB_SSL_MODE = self._value(
            env,
            "DB_SSL_MODE",
            "required" if self.APP_ENV in {"staging", "production"} else "disabled",
        ).strip().lower()
        if self.DB_SSL_MODE not in self.VALID_SSL_MODES:
            choices = ", ".join(sorted(self.VALID_SSL_MODES))
            raise RuntimeError(f"DB_SSL_MODE must be one of: {choices}")
        self.DB_SSL_CA = self._value(env, "DB_SSL_CA", "").strip() or None
        self.DB_SSL_CERT = self._value(env, "DB_SSL_CERT", "").strip() or None
        self.DB_SSL_KEY = self._value(env, "DB_SSL_KEY", "").strip() or None
        if self.DB_SSL_MODE in {"verify_ca", "verify_identity"} and not self.DB_SSL_CA:
            raise RuntimeError(f"DB_SSL_CA is required when DB_SSL_MODE={self.DB_SSL_MODE}")

    @staticmethod
    def _value(env: Mapping[str, str], name: str, default: str) -> str:
        value = env.get(name)
        return default if value is None else value

    @staticmethod
    def _first_nonempty(
        env: Mapping[str, str], *names: str, default: str | None = None
    ) -> str:
        for name in names:
            value = env.get(name)
            if value is not None and value.strip():
                return value.strip()
        if default is None:
            raise RuntimeError(f"One of {', '.join(names)} must be set")
        return default

    @staticmethod
    def _first_present(
        env: Mapping[str, str], *names: str, default: str = ""
    ) -> str:
        for name in names:
            if name in env:
                return env[name]
        return default

    @staticmethod
    def _parse_origins(raw: str) -> list[str]:
        origins: list[str] = []
        for item in raw.split(","):
            if not item.strip():
                continue
            origin = normalise_origin(item)
            if origin not in origins:
                origins.append(origin)
        return origins

    def _build_database_url(self, env: Mapping[str, str]) -> URL:
        raw_url = self._first_nonempty(
            env, "DATABASE_URL", "MYSQL_URL", default=""
        )
        if raw_url:
            try:
                url = make_url(raw_url)
            except ValueError as exc:
                raise RuntimeError(
                    "DATABASE_URL/MYSQL_URL contains an invalid port or syntax"
                ) from exc
            except Exception as exc:
                raise RuntimeError("DATABASE_URL/MYSQL_URL is not a valid database URL") from exc
            if url.drivername == "mysql":
                url = url.set(drivername="mysql+pymysql")
            if url.drivername != "mysql+pymysql":
                raise RuntimeError("Only mysql:// or mysql+pymysql:// database URLs are supported")
            if not url.host or not url.database:
                raise RuntimeError("Database URL must include a host and database name")
            try:
                url_port = url.port or 3306
            except ValueError as exc:
                raise RuntimeError("Database URL contains an invalid port") from exc
            if not 1 <= url_port <= 65535:
                raise RuntimeError("Database URL port must be in the range 1..65535")
            query = dict(url.query)
            unsupported_query = set(query) - {"charset"}
            if unsupported_query:
                names = ", ".join(sorted(unsupported_query))
                raise RuntimeError(
                    "Database URL query parameters are controlled by dedicated "
                    f"settings; unsupported: {names}"
                )
            charset = query.get("charset", "utf8mb4")
            if not isinstance(charset, str) or charset.lower() != "utf8mb4":
                raise RuntimeError("Database URL charset must be utf8mb4")
            url = url.set(query={"charset": "utf8mb4"})
        else:
            host = self._first_nonempty(
                env, "DB_HOST", "MYSQLHOST", "MYSQL_HOST", default="127.0.0.1"
            )
            port = _parse_int(
                self._first_nonempty(
                    env, "DB_PORT", "MYSQLPORT", "MYSQL_PORT", default="3306"
                ),
                "DB_PORT",
                1,
                65535,
            )
            user = self._first_nonempty(
                env, "DB_USER", "MYSQLUSER", "MYSQL_USER", default="root"
            )
            password = self._first_present(
                env, "DB_PASSWORD", "MYSQLPASSWORD", "MYSQL_PASSWORD", default=""
            )
            database = self._first_nonempty(
                env,
                "DB_NAME",
                "MYSQLDATABASE",
                "MYSQL_DATABASE",
                default="coseat18",
            )
            url = URL.create(
                drivername="mysql+pymysql",
                username=user,
                password=password,
                host=host,
                port=port,
                database=database,
                query={"charset": "utf8mb4"},
            )

        self.DATABASE_URL = raw_url or None
        self.DB_HOST = url.host or ""
        try:
            resolved_port = url.port or 3306
        except ValueError as exc:
            raise RuntimeError("Database URL contains an invalid port") from exc
        self.DB_PORT = str(resolved_port)
        self.DB_USER = url.username or ""
        self.DB_PASSWORD = url.password or ""
        self.DB_NAME = url.database or ""
        return url

    @property
    def database_url(self) -> URL:
        return self._database_url

    @property
    def database_connect_args(self) -> dict:
        args: dict = {"connect_timeout": self.DB_CONNECT_TIMEOUT}
        if self.DB_SSL_MODE == "disabled":
            args["ssl_disabled"] = True
        elif self.DB_SSL_MODE == "required":
            args["ssl"] = {"check_hostname": False}
        else:
            args.update(
                {
                    "ssl_ca": self.DB_SSL_CA,
                    "ssl_cert": self.DB_SSL_CERT,
                    "ssl_key": self.DB_SSL_KEY,
                    "ssl_verify_cert": True,
                    "ssl_verify_identity": self.DB_SSL_MODE == "verify_identity",
                }
            )
        return {key: value for key, value in args.items() if value is not None}

    def validate_for_startup(self) -> None:
        weak_secrets = {
            "",
            "change-me",
            "replace-with-a-long-random-string",
            "development-secret",
            "test-secret",
        }
        encoded_secret = self.SESSION_SECRET.encode("utf-8")
        if (
            self.SESSION_SECRET.strip().lower() in weak_secrets
            or len(encoded_secret) < 32
            or len(set(self.SESSION_SECRET)) < 8
        ):
            raise RuntimeError(
                "SESSION_SECRET must be a unique random value of at least 32 UTF-8 bytes"
            )
        if self.SESSION_COOKIE_SAMESITE == "none" and not self.SESSION_COOKIE_SECURE:
            raise RuntimeError("SameSite=None session cookies must set SESSION_COOKIE_SECURE=1")
        if self.APP_ENV in {"staging", "production"}:
            if self.DEBUG:
                raise RuntimeError("DEBUG must be disabled in staging and production")
            if not self.SESSION_COOKIE_SECURE:
                raise RuntimeError("Secure session cookies are required in staging and production")
            if not self._allowed_origins_explicit or not self.allowed_origins:
                raise RuntimeError(
                    "ALLOWED_ORIGINS must be explicitly configured in staging and production"
                )
            if any(not origin.startswith("https://") for origin in self.allowed_origins):
                raise RuntimeError(
                    "ALLOWED_ORIGINS must use HTTPS in staging and production"
                )


settings = Settings()
