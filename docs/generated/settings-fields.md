<!-- Generated from: apps\api\app\core\config.py — do not edit manually -->

## Environment variables (from Settings)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `API_V1_STR` | `str` | '/api/v1' |  |
| `SECRET_KEY` | `str` | secrets.token_urlsafe(32) |  |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | 60 * 24 * 8 |  |
| `FRONTEND_HOST` | `str` | 'http://localhost:5173' |  |
| `ENVIRONMENT` | `Literal['local', 'staging', 'production']` | 'local' |  |
| `BACKEND_CORS_ORIGINS` | `Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)]` | [] |  |
| `PROJECT_NAME` | `str` |  |  |
| `SENTRY_DSN` | `HttpUrl | None` | None |  |
| `POSTGRES_SERVER` | `str` |  |  |
| `POSTGRES_PORT` | `int` | 5432 |  |
| `POSTGRES_USER` | `str` |  |  |
| `POSTGRES_PASSWORD` | `str` | '' |  |
| `POSTGRES_DB` | `str` | '' |  |
| `SMTP_TLS` | `bool` | True |  |
| `SMTP_SSL` | `bool` | False |  |
| `SMTP_PORT` | `int` | 587 |  |
| `SMTP_HOST` | `str | None` | None |  |
| `SMTP_USER` | `str | None` | None |  |
| `SMTP_PASSWORD` | `str | None` | None |  |
| `EMAILS_FROM_EMAIL` | `EmailStr | None` | None |  |
| `EMAILS_FROM_NAME` | `str | None` | None |  |
| `EMAIL_RESET_TOKEN_EXPIRE_HOURS` | `int` | 48 |  |
| `EMAIL_TEST_USER` | `EmailStr` | 'test@example.com' |  |
| `FIRST_SUPERUSER` | `EmailStr` |  |  |
| `FIRST_SUPERUSER_PASSWORD` | `str` |  |  |
