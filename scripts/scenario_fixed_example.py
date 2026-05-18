"""
Scenario 2: Fixed example prediction
Loads a predefined image (a dummy tensor or a saved synthetic image) to ensure
the prediction pipeline works deterministically and outputs expected types.
"""
import logging
from pathlib import Path
import torch
from PIL import Image
import numpy as np

from etl.inference import PlantDiseasePredictor
from etl.config.helpers import PROJECT_ROOT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("scenario_fixed_example")

def create_dummy_image(path: Path):
    """Creates a simple 224x224 RGB image."""
    img_array = np.zeros((224, 224, 3), dtype=np.uint8)
    # Add a green square in the middle to simulate a leaf
    img_array[60:160, 60:160] = [34, 139, 34]
    img = Image.fromarray(img_array)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)

def main():
    model_path = PROJECT_ROOT / "data" / "checkpoints" / "model.pt"
    dummy_img_path = PROJECT_ROOT / "data" / "raw" / "dummy_leaf.jpg"
    
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}.")
        return

    logger.info(f"1. Preparing fixed example image at {dummy_img_path}...")
    create_dummy_image(dummy_img_path)
    
    logger.info("2. Loading model...")
    predictor = PlantDiseasePredictor(model_path)
    predictor.load_model()
    
    logger.info("3. Preprocessing image...")
    img = Image.open(dummy_img_path).convert("RGB")
    tensor = predictor.transform(img).unsqueeze(0).to(predictor.device)
    
    logger.info("4. Running prediction...")
    with torch.no_grad():
        out = predictor.model(tensor)
        prob = torch.sigmoid(out).item()
        pred_class = 1 if prob > 0.5 else 0
        
    logger.info(f"Prediction for fixed example: Class={pred_class}, Confidence={prob:.4f}")
    
    # Assert output types
    assert isinstance(pred_class, int), "Prediction class should be an integer"
    assert isinstance(prob, float), "Confidence should be a float"
    logger.info("Output types validated.")

if __name__ == "__main__":
    main()
