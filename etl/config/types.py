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
    term_id: int = 9       # Plant health/disease
    term_value_id: int = 11  # Diseased
    per_page: int = Field(200, gt=0, le=200)
    max_pages: int = Field(10, gt=0)
    rate_limit_seconds: float = Field(2.0, ge=0)


class KaggleSourceConfig(BaseModel):
    enabled: bool = False
    dataset: str = ""


class SourcesConfig(BaseModel):
    inaturalist: iNaturalistSourceConfig
    kaggle: KaggleSourceConfig


class LoadConfig(BaseModel):
    format: Literal["sqlite", "parquet", "csv"] = "sqlite"
    target_path: str = "data/processed/observations.db"
    table_name: str = "observations"


class AppConfig(BaseModel):
    general: GeneralConfig
    sources: SourcesConfig
    load: LoadConfig
