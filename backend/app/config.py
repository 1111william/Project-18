import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "coseat18")

    SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CROSS_SITE_COOKIE = os.getenv("CROSS_SITE_COOKIE", "0")
    DEBUG = os.getenv("DEBUG", "1")

    MAX_CHILDREN_PER_PARENT = int(os.getenv("MAX_CHILDREN_PER_PARENT", "5"))

    @property
    def database_url(self):
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def allowed_origins(self):
        raw = os.getenv("ALLOWED_ORIGINS", self.FRONTEND_URL)
        return [item.strip() for item in raw.split(",") if item.strip()]


settings = Settings()
