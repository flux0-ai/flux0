import enum
from typing import List, Union

from flux0_api.auth import AuthType
from flux0_core.logging import LogLevel
from flux0_core.storage.types import StorageType
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvType(enum.Enum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="FLUX0_", enable_decoding=False, extra="allow"
    )
    env: EnvType = Field(default=EnvType.PRODUCTION)
    port: int = Field(default=8080)
    auth_type: AuthType = Field(default_factory=lambda: AuthType.NOOP)
    log_level: LogLevel = Field(default_factory=lambda: LogLevel.INFO)
    stores_type: StorageType = Field(default_factory=lambda: StorageType.NANODB_MEMORY)
    modules: List[str] = Field(default_factory=list)

    @field_validator("modules", mode="before")
    @classmethod
    def decode_modules(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [module.strip() for module in v.split(",") if module.strip()]
        return v


settings = Settings()
