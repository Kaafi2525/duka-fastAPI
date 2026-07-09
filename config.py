import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


load_dotenv()


def _split_csv(value: str, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(',') if item.strip()]


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv('APP_NAME', 'Moha Duka API')
    base_url: str = os.getenv('BASE_URL', 'http://127.0.0.1:8000')
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./moha_duka.db')
    secret_key: str = os.getenv('SECRET_KEY', 'change-me-in-env')
    algorithm: str = os.getenv('JWT_ALGORITHM', 'HS256')
    access_token_minutes: int = int(os.getenv('ACCESS_TOKEN_MINUTES', '30'))
    refresh_token_days: int = int(os.getenv('REFRESH_TOKEN_DAYS', '7'))
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv(
                'CORS_ORIGINS',
                'http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:5500,null',
            ),
            ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://127.0.0.1:5500', 'null'],
        )
    )
    cookie_secure: bool = _as_bool(os.getenv('COOKIE_SECURE'), False)
    cookie_samesite: str = os.getenv('COOKIE_SAMESITE', 'lax')
    mpesa_consumer_key: str = os.getenv('MPESA_CONSUMER_KEY', '')
    mpesa_consumer_secret: str = os.getenv('MPESA_CONSUMER_SECRET', '')
    mpesa_short_code: str = os.getenv('MPESA_SHORT_CODE', '174379')
    mpesa_passkey: str = os.getenv('MPESA_PASSKEY', '')
    mpesa_stk_push_url: str = os.getenv(
        'MPESA_STK_PUSH_URL',
        'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
    )
    mpesa_auth_url: str = os.getenv(
        'MPESA_AUTH_URL',
        'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
    )
    mailtrap_token: str = os.getenv('MAILTRAP_TOKEN', '')
    mailtrap_sender_email: str = os.getenv(
        'MAILTRAP_SENDER_EMAIL',
        'no-reply@moha-duka.local',
    )
    mailtrap_sender_name: str = os.getenv('MAILTRAP_SENDER_NAME', 'Moha Duka')

    @property
    def mpesa_callback_url(self) -> str:
        return f'{self.base_url.rstrip()}/mpesa/stk-call-back'


settings = Settings()

