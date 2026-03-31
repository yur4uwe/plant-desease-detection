from typing import TypedDict


class GeneralConfig(TypedDict):
    download_images: bool
    log_level: str
    raw_data_path: str
    processed_data_path: str


class iNaturalistSourceConfig(TypedDict):
    enabled: bool
    base_url: str
    taxon_id: int
    term_id: int
    per_page: int
    max_pages: int
    rate_limit_seconds: float


class KaggleSourceConfig(TypedDict):
    enabled: bool
    dataset: str


class SourcesConfig(TypedDict):
    inaturalist: iNaturalistSourceConfig
    kaggle: KaggleSourceConfig


class LoadConfig(TypedDict):
    format: str
    target_path: str
    table_name: str


class AppConfig(TypedDict):
    general: GeneralConfig
    sources: SourcesConfig
    load: LoadConfig
