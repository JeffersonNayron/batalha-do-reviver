import os
from pathlib import Path
from functools import lru_cache
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseModel):
    # Preview without a managed database uses ephemeral storage. Public reads work,
    # but persistence/admin must remain disabled until DATABASE_URL is configured.
    database_url: str = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL') or (
        "sqlite:////tmp/reviver.db" if os.getenv("VERCEL") else f'sqlite:///{ROOT / "reviver.db"}'
    )
    admin_password_hash: str = os.getenv('ADMIN_PASSWORD_HASH', '')
    admin_username: str = os.getenv('ADMIN_USERNAME', 'admin').strip().casefold()
    admin_email: str = os.getenv('ADMIN_EMAIL', '')
    session_secret: str = os.getenv('SESSION_SECRET', '')
    production: bool = os.getenv('APP_ENV') == 'production' or bool(os.getenv('VERCEL'))
    public_base_url: str = os.getenv('PUBLIC_BASE_URL', '').rstrip('/')
    allowed_origin: str = os.getenv('ALLOWED_ORIGIN', '')

@lru_cache
def get_settings() -> Settings:
    return Settings()
