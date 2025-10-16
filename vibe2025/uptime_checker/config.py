import json
from pathlib import Path
from typing import Any
from pydantic import Field, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application configuration with JSON file support."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_prefix="MONITOR_"
    )

    check_interval_seconds: int = Field(
        default=60,
        description="Interval between checks in seconds",
        ge=1
    )
    connection_timeout_seconds: float = Field(
        default=5.0,
        description="Connection timeout in seconds",
        gt=0
    )
    services_file: str = Field(
        default="config.json",
        description="Path to services configuration JSON file"
    )
    results_file: str = Field(
        default="results.json",
        description="Path to results output JSON file"
    )

    _services_config_path: Path | None = PrivateAttr(default=None)

    def __init__(self, services_config_path: str | None = None, **kwargs):
        """Initialize config with optional services file path."""
        if services_config_path:
            self._services_config_path = Path(services_config_path)
        super().__init__(**kwargs)

    def load_services(self) -> list[tuple[str, int]]:
        """Load services from JSON configuration file."""
        config_path = self._services_config_path or Path(self.services_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Services config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        services = data.get("services", [])
        return [(svc["host"], svc["port"]) for svc in services]
