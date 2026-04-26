import pytest
from pathlib import Path
from etl.config.types import YoloSourceConfig
from etl.sources.yolo import YoloSource

def test_yolo_source_logic():
    # We'll use a mock root_path for this test if needed, 
    # but here we can just test the parsing logic if we simulate the files.
    config = YoloSourceConfig(
        enabled=True,
        name="test_yolo",
        root_path="data/raw/mcdd/Multi-Crop Disease Dataset/Multicrop Disease Dataset/Multicrop Disease Dataset",
        provenance="Field"
    )
    source = YoloSource(config)
    
    # Test YAML parsing
    yaml_path = source.root_path / "data.yaml"
    if yaml_path.exists():
        names = source._parse_yaml_names(yaml_path)
        assert len(names) == 30
        assert names[0] == 'banana_bract_mosaic_virus'
        assert names[21] == 'groundnut_healthy'
        assert names[28] == 'radish_healthy'
    else:
        pytest.skip("MCDD data.yaml not found, skipping deep test")

def test_yolo_extraction_sample():
    config = YoloSourceConfig(
        enabled=True,
        name="mcdd_india",
        root_path="data/raw/mcdd/Multi-Crop Disease Dataset/Multicrop Disease Dataset/Multicrop Disease Dataset",
        provenance="Field"
    )
    source = YoloSource(config)
    
    # Check a few actual files if they exist
    count = 0
    for obs in source.fetch():
        assert obs.label is not None
        assert obs.label != "IMG"  # THE CORE FIX
        assert obs.label != "Unknown"
        
        # Check is_diseased logic
        if "healthy" in obs.label.lower():
            assert obs.is_diseased == False
        else:
            assert obs.is_diseased == True
            
        count += 1
        if count > 10:
            break
    
    if count == 0:
        pytest.skip("No YOLO files found to test")
