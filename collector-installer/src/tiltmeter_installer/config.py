from __future__ import annotations

import secrets
import shutil
from dataclasses import dataclass
from pathlib import Path

from tiltmeter_installer.certs import generate_self_signed_cert
from tiltmeter_installer.paths import template_dir


DEFAULT_COLLECTOR_IMAGE = "ghcr.io/neotech-australia/tiltmeter-platform/collector:latest"
DEFAULT_DASHBOARD_IMAGE = "ghcr.io/neotech-australia/tiltmeter-platform/dashboard:latest"


@dataclass(frozen=True)
class InstallSettings:
    install_dir: Path
    dashboard_port: int
    collector_image: str = DEFAULT_COLLECTOR_IMAGE
    dashboard_image: str = DEFAULT_DASHBOARD_IMAGE


@dataclass(frozen=True)
class InstallResult:
    install_dir: Path
    env_file: Path
    compose_file: Path
    credentials_file: Path
    dashboard_url: str
    admin_username: str
    admin_password: str


def random_hex(bytes_count: int = 32) -> str:
    return secrets.token_hex(bytes_count)


def random_password() -> str:
    return secrets.token_urlsafe(24)


def cors_origins(port: int) -> str:
    origins = [
        "https://localhost",
        "https://127.0.0.1",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    if port != 443:
        origins.extend([f"https://localhost:{port}", f"https://127.0.0.1:{port}"])
    return ",".join(origins)


def read_env_file(env_file: Path) -> dict[str, str]:
    if not env_file.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def write_env(settings: InstallSettings) -> tuple[Path, dict[str, str]]:
    env_file = settings.install_dir / ".env"
    existing = read_env_file(env_file)
    postgres_password = existing.get("POSTGRES_PASSWORD") or random_password()
    admin_password = existing.get("ADMIN_PASSWORD") or "admin"
    jwt_secret = existing.get("JWT_SECRET_KEY") or random_hex(32)

    values = {
        "ENVIRONMENT": "production",
        "COLLECTOR_IMAGE": settings.collector_image,
        "DASHBOARD_IMAGE": settings.dashboard_image,
        "DASHBOARD_PORT": str(settings.dashboard_port),
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "API_VERSION": "1.0.0",
        "UVICORN_LOG_LEVEL": "info",
        "CORS_ORIGINS": cors_origins(settings.dashboard_port),
        "SWAGGER_DOCS_URL": "/docs",
        "OPENAPI_URL": "/openapi.json",
        "API_SSL_CERTFILE": "/app/certs/localhost.pem",
        "API_SSL_KEYFILE": "/app/certs/localhost-key.pem",
        "JWT_SECRET_KEY": jwt_secret,
        "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "REFRESH_COOKIE_NAME": "collector_refresh_token",
        "REFRESH_COOKIE_PATH": "/admin",
        "ALLOW_INSECURE_JWT_SECRET": "false",
        "POSTGRES_DB": "lora",
        "POSTGRES_USER": "tiltmeter",
        "POSTGRES_PASSWORD": postgres_password,
        "DATABASE_URL": f"postgresql://tiltmeter:{postgres_password}@postgres:5432/lora",
        "SQL_ECHO": "false",
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": admin_password,
        "DEFAULT_MQTT_HOST": "192.168.230.1",
        "DEFAULT_MQTT_SERVER_PORT": "1883",
        "DEFAULT_MQTT_SUBSCRIBE_TOPIC": "application/#",
        "DEFAULT_MQTT_VERSION": "v3.1.1",
        "DEFAULT_LOG_RETENTION_DAYS": "30",
        "DEFAULT_LOG_MAX_ROWS": "10000",
        "DEFAULT_CLOUD_AUTH_API_URL": "https://api.neogt.com.au/auth/api-client/authenticate",
        "DEFAULT_CLOUD_SYNC_API_URL": "https://api.neogt.com.au/devices/readings",
    }

    lines = [f"{key}={value}" for key, value in values.items()]
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        env_file.chmod(0o600)
    except OSError:
        pass
    return env_file, values


def write_credentials(settings: InstallSettings, values: dict[str, str]) -> Path:
    credentials_file = settings.install_dir / "credentials.txt"
    credentials_file.write_text(
        "\n".join(
            [
                "Tiltmeter Platform credentials",
                "",
                f"Dashboard URL: https://localhost:{settings.dashboard_port}",
                f"Admin username: {values['ADMIN_USERNAME']}",
                f"Admin password: {values['ADMIN_PASSWORD']}",
                "",
                f"Postgres user: {values['POSTGRES_USER']}",
                f"Postgres password: {values['POSTGRES_PASSWORD']}",
                "",
                "Keep this file private. It is generated locally by the installer.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    try:
        credentials_file.chmod(0o600)
    except OSError:
        pass
    return credentials_file


def create_installation(settings: InstallSettings) -> InstallResult:
    settings.install_dir.mkdir(parents=True, exist_ok=True)
    (settings.install_dir / "certs").mkdir(exist_ok=True)

    compose_file = settings.install_dir / "docker-compose.yml"
    shutil.copyfile(template_dir() / "docker-compose.production.yml", compose_file)
    cert_file = settings.install_dir / "certs" / "localhost.pem"
    key_file = settings.install_dir / "certs" / "localhost-key.pem"
    if not cert_file.is_file() or not key_file.is_file():
        generate_self_signed_cert(settings.install_dir / "certs")
    env_file, values = write_env(settings)
    credentials_file = write_credentials(settings, values)
    return InstallResult(
        install_dir=settings.install_dir,
        env_file=env_file,
        compose_file=compose_file,
        credentials_file=credentials_file,
        dashboard_url=f"https://localhost:{settings.dashboard_port}",
        admin_username=values["ADMIN_USERNAME"],
        admin_password=values["ADMIN_PASSWORD"],
    )
