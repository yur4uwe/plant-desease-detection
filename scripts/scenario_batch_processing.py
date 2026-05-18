"""
Scenario 3: Batch processing simulation
Simulates processing a batch of images (e.g. from a daily drop folder),
without going through the database, useful for offline analytics.
"""
import logging
import time
from pathlib import Path
import torch
from PIL import Image
import os
import random
import numpy as np

from etl.inference import PlantDiseasePredictor
from etl.config.helpers import PROJECT_ROOT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("scenario_batch_processing")

def main():
    model_path = PROJECT_ROOT / "data" / "checkpoints" / "model.pt"
    # Find a directory with some raw images, or mock a few
    raw_dir = PROJECT_ROOT / "data" / "raw"
    
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}.")
        return

    logger.info("1. Searching for images for batch processing...")
    # Gather up to 20 images from raw dir
    image_paths = []
    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        image_paths.extend(list(raw_dir.rglob(ext)))
        
    # Pick a random subset to simulate a batch
    if len(image_paths) > 20:
        image_paths = random.sample(image_paths, 20)
        
    if not image_paths:
        logger.warning("No images found in raw data directory. Generating mock batch.")
        # Generate some mock images
        batch_dir = PROJECT_ROOT / "data" / "raw" / "mock_batch"
        batch_dir.mkdir(parents=True, exist_ok=True)
        for i in range(5):
            path = batch_dir / f"mock_{i}.jpg"
            img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            Image.fromarray(img_array).save(path)
            image_paths.append(path)
            
    logger.info(f"Found {len(image_paths)} images for processing.")

    logger.info("2. Initializing model...")
    predictor = PlantDiseasePredictor(model_path)
    predictor.load_model()
    
    logger.info("3. Starting batch inference...")
    start_time = time.time()
    
    results = {"diseased": 0, "healthy": 0, "errors": 0}
    
    with torch.no_grad():
        for path in image_paths:
            try:
                img = Image.open(path).convert("RGB")
                tensor = predictor.transform(img).unsqueeze(0).to(predictor.device)
                out = predictor.model(tensor)
                prob = torch.sigmoid(out).item()
                pred_class = 1 if prob > 0.5 else 0
                
                if pred_class == 1:
                    results["diseased"] += 1
                else:
                    results["healthy"] += 1
            except Exception as e:
                logger.error(f"Failed to process {path}: {e}")
                results["errors"] += 1

    duration = time.time() - start_time
    logger.info(f"4. Batch processing complete in {duration:.2f} seconds.")
    logger.info(f"Summary: {results}")

if __name__ == "__main__":
    main()
