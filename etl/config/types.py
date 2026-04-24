from pydantic import BaseModel, Field, HttpUrl
from typing import Literal


class GeneralConfig(BaseModel):
    download_images: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    raw_data_path: str = "data/raw"
    processed_data_path: str = "data/processed"


class iNaturalistSourceConfig(BaseModel):
    enabled: bool = False
    refetch: bool = False
    base_url: HttpUrl = Field(..., description="API base URL")
    taxon_id: int = 47126  # Plantae
    project_ids: list[int] = Field(default_factory=list)
    per_page: int = Field(200, gt=0, le=200)
    max_pages: int = Field(10, gt=0)
    rate_limit_seconds: float = Field(2.0, ge=0)


class LocalSourceConfig(BaseModel):
    enabled: bool = False
    name: str = "local"
    root_path: str = "etl/data/raw/local"
    include_glob: str = "**/*.jpg"
    status_pattern: str | None = None
    diseased_values: list[str] = Field(default_factory=list)
    healthy_values: list[str] = Field(default_factory=list)
    healthy_regex: str | None = None
    diseased_regex: str | None = None
    default_is_diseased: bool = True
    provenance: Literal["Field", "Laboratory", "Unknown"] = "Unknown"


class LocalMetadataSourceConfig(BaseModel):
    enabled: bool = False
    name: str = "metadata_local"
    metadata_path: str = ""
    images_root: str = ""
    column_mapping: dict[str, str] = Field(default_factory=dict)
    healthy_regex: str | None = None
    default_is_diseased: bool = True
    provenance: Literal["Field", "Laboratory", "Unknown"] = "Unknown"


class SourcesConfig(BaseModel):
    inaturalist: iNaturalistSourceConfig
    local_sources: list[LocalSourceConfig] = Field(default_factory=list)
    metadata_sources: list[LocalMetadataSourceConfig] = Field(default_factory=list)


class LoadConfig(BaseModel):
    format: Literal["sqlite", "parquet", "csv"] = "sqlite"
    target_path: str = "data/processed/observations.db"
    table_name: str = "observations"


class AppConfig(BaseModel):
    general: GeneralConfig
    sources: SourcesConfig
    load: LoadConfig
