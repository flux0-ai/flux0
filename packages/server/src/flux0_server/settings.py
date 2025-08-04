import enum
from typing import List, Optional, Union
from urllib.parse import parse_qs, urlparse

from flux0_api.auth import AuthType
from flux0_core.logging import LogLevel
from flux0_core.storage.types import NanoDBStorageType, StorageType
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvType(enum.Enum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"


class ParsedStoreConfig(BaseModel):
    type: StorageType
    mode: Optional[NanoDBStorageType]
    uri: Optional[str] = None  # for mongodb
    database: Optional[str] = None  # for mongodb
    dir: Optional[str] = None  # for nanodb file


def parse_store_uri(uri: str) -> ParsedStoreConfig:
    parsed = urlparse(uri)
    scheme = parsed.scheme

    if scheme == "nanodb":
        mode = parsed.hostname or "memory"
        query = parse_qs(parsed.query)
        if mode == "memory":
            return ParsedStoreConfig(type=StorageType.NANODB, mode=NanoDBStorageType.MEMORY)
        elif mode == "json":
            dir_ = query.get("dir", [parsed.path or "./data/nanodb"])[0]
            return ParsedStoreConfig(type=StorageType.NANODB, mode=NanoDBStorageType.JSON, dir=dir_)
        else:
            raise ValueError(f"Unsupported nanodb mode: {mode}")

    elif scheme == "mongodb":
        db = parsed.path.strip("/") or "flux0"
        base_uri = f"{parsed.scheme}://{parsed.netloc}"
        return ParsedStoreConfig(type=StorageType.MONGODB, mode=None, uri=base_uri, database=db)

    raise ValueError(f"Unsupported db_uri scheme: {scheme}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="FLUX0_", enable_decoding=False, extra="allow"
    )
    env: EnvType = Field(default=EnvType.PRODUCTION)
    port: int = Field(default=8080)
    auth_type: AuthType = Field(default_factory=lambda: AuthType.NOOP)
    log_level: LogLevel = Field(default_factory=lambda: LogLevel.INFO)
    db_uri: str = Field(default="nanodb://memory")
    modules: List[str] = Field(default_factory=list)

    @field_validator("modules", mode="before")
    @classmethod
    def decode_modules(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [module.strip() for module in v.split(",") if module.strip()]
        return v

    @model_validator(mode="after")
    def populate_db_config(self) -> "Settings":
        self.db = parse_store_uri(self.db_uri)
        return self


settings = Settings()
