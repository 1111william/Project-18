"""Tests never load deployment credentials from a developer's backend/.env."""

import os
os.environ["PYTHON_DOTENV_DISABLED"] = "1"


# Only defaults for test setup. Integration tests require an explicit opt-in
# and independently verify the actual target before any database writes.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SESSION_SECRET", "unit-tests-Only-73dcbe94106a528f896410a3")
os.environ.setdefault("DEBUG", "0")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("SESSION_COOKIE_SECURE", "0")
os.environ.setdefault("DB_SSL_MODE", "disabled")
