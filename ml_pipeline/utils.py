from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def resolve_image_path(row_or_dict: dict) -> Optional[Path]:
    """
    Resolves the local file path for an image given its observation data.
    Expects a dictionary-like object with at least 'image_url', 'source', and 'external_id'.
    """
    image_url_str = row_or_dict.get("image_url")
    if not image_url_str:
        return None
        
    p = PROJECT_ROOT / image_url_str
    if p.exists():
        return p

    # Generic fallback for local datasets with train/val/test/valid splits
    fname = Path(image_url_str).name
    source_dirs = {
        "meta_plantseg": "data/raw/plantseg/plantseg/images",
        "yolo_mcdd_india": "data/raw/mcdd/Multi-Crop Disease Dataset/Multicrop Disease Dataset/Multicrop Disease Dataset",
        "local_ccmt_ghana": "data/raw/ccmt",
    }

    source = row_or_dict.get("source")
    if source in source_dirs:
        base_search = PROJECT_ROOT / source_dirs[source]
        for sub in [
            "",
            "train",
            "val",
            "valid",
            "test",
            "train/images",
            "valid/images",
            "test/images",
        ]:
            p_alt = base_search / sub / fname
            if p_alt.exists():
                return p_alt

    # Fallback for inaturalist
    external_id = row_or_dict.get("external_id")
    if external_id:
        p_inat = (
            PROJECT_ROOT
            / "data"
            / "raw"
            / "inaturalist"
            / "images"
            / f"{external_id}.jpg"
        )
        if p_inat.exists():
            return p_inat
            
    return None
