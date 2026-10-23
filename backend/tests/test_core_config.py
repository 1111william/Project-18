import os
from pathlib import Path
import unittest


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "SESSION_SECRET",
    "T9!vQ2#kLm7$Np4@Rs8%Wx3&Yz6*Bc1-Df5+Gh0",
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("DB_SSL_MODE", "disabled")

from backend.app.config import ENV_FILE, Settings
from pymysql.connections import Connection


SECRET = "T9!vQ2#kLm7$Np4@Rs8%Wx3&Yz6*Bc1-Df5+Gh0"


def base_env(**overrides):
    env = {
        "APP_ENV": "test",
        "SESSION_SECRET": SECRET,
        "ALLOWED_ORIGINS": "http://localhost:5173",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "3306",
        "DB_USER": "root",
        "DB_PASSWORD": "",
        "DB_NAME": "test_db",
        "DB_SSL_MODE": "disabled",
    }
    env.update(overrides)
    return env


class SettingsTests(unittest.TestCase):
    def test_env_file_is_explicitly_backend_dotenv(self):
        self.assertEqual(ENV_FILE, Path(__file__).resolve().parents[1] / ".env")

    def test_structured_database_fields_preserve_special_password(self):
        settings = Settings(base_env(DB_PASSWORD="p@ss:/?#word"))

        self.assertEqual(settings.database_url.password, "p@ss:/?#word")
        self.assertEqual(settings.database_url.drivername, "mysql+pymysql")
        self.assertEqual(settings.database_url.query["charset"], "utf8mb4")

    def test_database_url_has_priority_and_normalises_mysql_driver(self):
        env = base_env(
            DATABASE_URL="mysql://url-user:p%40ss%3Aword@db.example:3307/url_db",
            DB_HOST="ignored.example",
        )
        settings = Settings(env)

        self.assertEqual(settings.database_url.drivername, "mysql+pymysql")
        self.assertEqual(settings.DB_HOST, "db.example")
        self.assertEqual(settings.DB_PORT, "3307")
        self.assertEqual(settings.DB_PASSWORD, "p@ss:word")
        self.assertEqual(settings.DB_NAME, "url_db")

    def test_database_url_cannot_override_tls_or_charset_controls(self):
        with self.assertRaisesRegex(RuntimeError, "unsupported: ssl_disabled"):
            Settings(
                base_env(
                    DATABASE_URL=(
                        "mysql://user:password@db.example/app?ssl_disabled=true"
                    )
                )
            )
        with self.assertRaisesRegex(RuntimeError, "charset must be utf8mb4"):
            Settings(
                base_env(
                    DATABASE_URL="mysql://user:password@db.example/app?charset=latin1"
                )
            )

    def test_database_url_rejects_invalid_ports_during_startup(self):
        with self.assertRaisesRegex(RuntimeError, "invalid port"):
            Settings(
                base_env(
                    DATABASE_URL="mysql://user:password@db.example:not-a-port/app"
                )
            )
        with self.assertRaisesRegex(RuntimeError, "range 1..65535"):
            Settings(
                base_env(
                    DATABASE_URL="mysql://user:password@db.example:70000/app"
                )
            )

    def test_railway_aliases_are_supported(self):
        env = {
            "APP_ENV": "test",
            "SESSION_SECRET": SECRET,
            "ALLOWED_ORIGINS": "http://localhost:5173",
            "MYSQLHOST": "railway.mysql.internal",
            "MYSQLPORT": "3307",
            "MYSQLUSER": "railway",
            "MYSQLPASSWORD": "rail@way",
            "MYSQLDATABASE": "railway_db",
            "DB_SSL_MODE": "disabled",
        }

        settings = Settings(env)

        self.assertEqual(settings.DB_HOST, "railway.mysql.internal")
        self.assertEqual(settings.DB_PORT, "3307")
        self.assertEqual(settings.DB_USER, "railway")
        self.assertEqual(settings.DB_PASSWORD, "rail@way")
        self.assertEqual(settings.DB_NAME, "railway_db")

    def test_tls_modes_map_to_pymysql_connect_args(self):
        required = Settings(base_env(DB_SSL_MODE="required"))
        verified = Settings(
            base_env(DB_SSL_MODE="verify_identity", DB_SSL_CA="/run/secrets/rds-ca.pem")
        )

        self.assertEqual(required.database_connect_args["ssl"], {"check_hostname": False})
        self.assertTrue(verified.database_connect_args["ssl_verify_cert"])
        self.assertTrue(verified.database_connect_args["ssl_verify_identity"])
        self.assertEqual(verified.database_connect_args["ssl_ca"], "/run/secrets/rds-ca.pem")

        deferred = Connection(
            host="db.example",
            user="user",
            password="password",
            defer_connect=True,
            **required.database_connect_args,
        )
        self.assertTrue(deferred.ssl)
        self.assertTrue(deferred._ssl_required)

    def test_preferred_tls_mode_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "DB_SSL_MODE"):
            Settings(base_env(DB_SSL_MODE="preferred"))

    def test_verify_tls_requires_ca(self):
        with self.assertRaisesRegex(RuntimeError, "DB_SSL_CA"):
            Settings(base_env(DB_SSL_MODE="verify_ca"))

    def test_origins_are_exact_normalised_and_deduplicated(self):
        settings = Settings(
            base_env(
                ALLOWED_ORIGINS=(
                    "https://Example.com:443/, https://example.com, "
                    "http://localhost:5173"
                )
            )
        )

        self.assertEqual(
            settings.allowed_origins,
            ["https://example.com", "http://localhost:5173"],
        )

    def test_wildcard_or_origin_path_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "explicit"):
            Settings(base_env(ALLOWED_ORIGINS="*"))
        with self.assertRaisesRegex(RuntimeError, "scheme://host"):
            Settings(base_env(ALLOWED_ORIGINS="https://*.example.com"))
        with self.assertRaisesRegex(RuntimeError, "scheme://host"):
            Settings(base_env(ALLOWED_ORIGINS="https://example.com/path"))
        with self.assertRaisesRegex(RuntimeError, "Invalid origin"):
            Settings(base_env(ALLOWED_ORIGINS="https://[bad"))

    def test_secret_is_validated_in_test_environment(self):
        settings = Settings(base_env(SESSION_SECRET="a" * 64))

        with self.assertRaisesRegex(RuntimeError, "unique random"):
            settings.validate_for_startup()

    def test_production_requires_safe_debug_cookie_and_origins(self):
        production = Settings(
            base_env(
                APP_ENV="production",
                DEBUG="0",
                ALLOWED_ORIGINS="https://app.example.com",
                DB_SSL_MODE="required",
            )
        )
        production.validate_for_startup()
        self.assertTrue(production.SESSION_COOKIE_SECURE)

        debug = Settings(
            base_env(
                APP_ENV="production",
                DEBUG="1",
                ALLOWED_ORIGINS="https://app.example.com",
                DB_SSL_MODE="required",
            )
        )
        with self.assertRaisesRegex(RuntimeError, "DEBUG"):
            debug.validate_for_startup()

    def test_cross_site_cookie_requires_secure(self):
        settings = Settings(
            base_env(
                SESSION_COOKIE_SAMESITE="none",
                SESSION_COOKIE_SECURE="0",
            )
        )

        with self.assertRaisesRegex(RuntimeError, "SameSite=None"):
            settings.validate_for_startup()

    def test_session_cookie_name_must_be_an_http_token(self):
        valid = Settings(base_env(SESSION_COOKIE_NAME="__Host-coseat.session"))
        self.assertEqual(valid.SESSION_COOKIE_NAME, "__Host-coseat.session")

        for invalid in ("bad/name", "bad:name", "bad@name", "会话"):
            with self.subTest(cookie_name=invalid):
                with self.assertRaisesRegex(RuntimeError, "cookie-name"):
                    Settings(base_env(SESSION_COOKIE_NAME=invalid))


if __name__ == "__main__":
    unittest.main()
