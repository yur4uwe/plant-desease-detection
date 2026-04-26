import pytest
from pathlib import Path
from etl.config.types import LocalSourceConfig, LocalMetadataSourceConfig
from etl.sources.local import LocalSource
from etl.sources.local_metadata import LocalMetadataSource

def test_ccmt_ghana_labels():
    config = LocalSourceConfig(
        enabled=True,
        name="ccmt_ghana",
        root_path="data/raw/ccmt",
        include_glob="**/*.jpg",
        healthy_regex="[A-Z][a-z]+_healthy",
        label_regex=None,
        default_is_diseased=True,
        provenance="Field"
    )
    source = LocalSource(config)
    
    path1 = Path("data/raw/ccmt/Cashew_healthy/healthy10_.jpg")
    assert source._determine_label(path1) == "Cashew_healthy"
    
    path2 = Path("data/raw/ccmt/Tomato_leaf blight/IMG_123.jpg")
    assert source._determine_label(path2) == "Tomato_leaf blight"

def test_mcdd_india_labels():
    config = LocalSourceConfig(
        enabled=True,
        name="mcdd_india",
        root_path="data/raw/mcdd",
        include_glob="**/*.jpg",
        healthy_regex=".*_healthy",
        label_regex="(?P<label>[A-Za-z-]+)(?=[_-]\\d|_)",
        default_is_diseased=True,
        provenance="Field"
    )
    source = LocalSource(config)
    
    path1 = Path("data/raw/mcdd/train/images/Anthracnose-1-_jpg.rf.5b8c4b30d31c064e628d5e572f412553.jpg")
    assert source._determine_label(path1) == "Anthracnose"
    
    path2 = Path("data/raw/mcdd/train/images/Bacterial-Spot_-1-_jpg.rf.a48a9.jpg")
    assert source._determine_label(path2) == "Bacterial-Spot"
    
    # Let's ensure no false positive matches on root path parts
    path3 = Path("/home/user/Multi-Crop Disease Dataset/images/Anthracnose-1-_jpg.jpg")
    assert source._determine_label(path3) == "Anthracnose"

def test_plantseg_metadata():
    config = LocalMetadataSourceConfig(
        enabled=True,
        name="plantseg",
        metadata_path="data/raw/plantseg/plantseg/Metadata.csv",
        images_root="data/raw/plantseg/plantseg/images",
        column_mapping={ "external_id": "Name", "image_path": "Name", "status": "Disease", "label": "Disease" },
        default_is_diseased=True,
        provenance="Laboratory"
    )
    source = LocalMetadataSource(config)
    
    try:
        iterator = source.fetch()
        observations = []
        for _ in range(5):
            try:
                obs = next(iterator)
                observations.append(obs)
            except StopIteration:
                break
                
        if len(observations) > 0:
            obs = observations[0]
            assert obs.source == "meta_plantseg"
            assert obs.label is not None
            assert obs.is_diseased == True
    except FileNotFoundError:
        pytest.skip("Plantseg metadata file not found, skipping read test")
