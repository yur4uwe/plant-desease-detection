import os
import logging
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def get_exif_data(image_path):
    """Extracts EXIF data from an image file."""
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()
            if not exif:
                return None
            
            data = {}
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]
                    data[decoded] = gps_data
                else:
                    data[decoded] = value
            return data
    except Exception:
        return None

def format_coords(gps_info):
    """Converts GPSInfo to decimal degrees."""
    def to_decimal(value):
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)

    try:
        lat = to_decimal(gps_info["GPSLatitude"])
        if gps_info.get("GPSLatitudeRef") == "S":
            lat = -lat
            
        lon = to_decimal(gps_info["GPSLongitude"])
        if gps_info.get("GPSLongitudeRef") == "W":
            lon = -lon
            
        return lat, lon
    except Exception:
        return None

def scan_raw_data(root_dir="etl/data/raw"):
    logger.info(f"Scanning for EXIF metadata in {root_dir}...")
    
    stats = {
        "total_images": 0,
        "has_exif": 0,
        "has_gps": 0,
        "has_timestamp": 0
    }
    
    samples = []
    
    image_extensions = {".jpg", ".jpeg", ".JPG", ".JPEG"}
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            path = Path(root) / file
            if path.suffix in image_extensions:
                stats["total_images"] += 1
                
                exif = get_exif_data(path)
                if exif:
                    stats["has_exif"] += 1
                    
                    found_gps = False
                    found_time = False
                    
                    # Check Timestamp
                    dt = exif.get("DateTimeOriginal") or exif.get("DateTime")
                    if dt:
                        stats["has_timestamp"] += 1
                        found_time = True
                    
                    # Check GPS
                    gps = exif.get("GPSInfo")
                    if gps:
                        coords = format_coords(gps)
                        if coords:
                            stats["has_gps"] += 1
                            found_gps = True
                    
                    if found_gps or found_time:
                        samples.append({
                            "file": path.name,
                            "path": str(path.relative_to(root_dir)),
                            "coords": format_coords(gps) if gps else None,
                            "time": dt
                        })

    # Summary Output
    print("\n" + "=" * 50)
    print(" EXIF METADATA SCAN REPORT")
    print("=" * 50)
    print(f"Total Images Scanned: {stats['total_images']}")
    print(f"Images with EXIF:     {stats['has_exif']} ({stats['has_exif']/stats['total_images']:.1%})")
    print(f"Images with GPS:      {stats['has_gps']} ({stats['has_gps']/stats['total_images']:.1%})")
    print(f"Images with Time:     {stats['has_timestamp']} ({stats['has_timestamp']/stats['total_images']:.1%})")
    print("-" * 50)
    
    if samples:
        print("Metadata Samples (First 5):")
        for s in samples[:5]:
            print(f"  - {s['file']}:")
            print(f"    Path: {s['path']}")
            print(f"    GPS:  {s['coords']}")
            print(f"    Time: {s['time']}")
    else:
        print("No spatiotemporal metadata found in image files.")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    scan_raw_data()
