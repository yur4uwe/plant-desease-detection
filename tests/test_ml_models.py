import pytest
import torch
import numpy as np
from PIL import Image
from pathlib import Path

from etl.inference import PlantDiseasePredictor
from ml_pipeline.evaluate import evaluate_gate
from ml_pipeline.train import train_deep_learning

@pytest.fixture
def mock_image_path(tmp_path):
    img_path = tmp_path / "test_img.jpg"
    img_array = np.zeros((224, 224, 3), dtype=np.uint8)
    Image.fromarray(img_array).save(img_path)
    return img_path

@pytest.fixture
def corrupted_image_path(tmp_path):
    img_path = tmp_path / "corrupted.jpg"
    with open(img_path, "wb") as f:
        f.write(b"not an image file")
    return img_path

@pytest.fixture
def empty_model_path(tmp_path):
    return tmp_path / "non_existent_model.pt"

@pytest.fixture
def mock_predictor(mock_image_path):
    # Setup predictor with a dummy model
    predictor = PlantDiseasePredictor(Path("dummy_path"))
    
    # Create a mock PyTorch model for testing outputs without full weights
    class DummyModel(torch.nn.Module):
        def forward(self, x):
            return torch.tensor([[0.8]]) # Outputs a raw logit > 0 (prob > 0.5)

    predictor.model = DummyModel()
    predictor.device = torch.device("cpu")
    return predictor

def test_inference_output_types(mock_predictor, mock_image_path):
    img = Image.open(mock_image_path).convert("RGB")
    tensor = mock_predictor.transform(img).unsqueeze(0).to(mock_predictor.device)
    
    with torch.no_grad():
        out = mock_predictor.model(tensor)
        prob = torch.sigmoid(out).item()
        pred_class = 1 if prob > 0.5 else 0
        
    assert isinstance(pred_class, int)
    assert isinstance(prob, float)
    assert pred_class in [0, 1]

def test_invalid_data_handling(mock_predictor, corrupted_image_path):
    # Ensure standard PIL handling throws an error on corrupted image
    with pytest.raises(Exception):
        Image.open(corrupted_image_path).convert("RGB")

def test_model_not_found(empty_model_path):
    predictor = PlantDiseasePredictor(empty_model_path)
    with pytest.raises(FileNotFoundError):
        predictor.load_model()

def test_extreme_dimensions(mock_predictor, tmp_path):
    # Create a 1x1 image (extreme dimension)
    img_path = tmp_path / "tiny.jpg"
    img_array = np.zeros((1, 1, 3), dtype=np.uint8)
    Image.fromarray(img_array).save(img_path)
    
    img = Image.open(img_path).convert("RGB")
    # The transform should resize it correctly to 224x224
    tensor = mock_predictor.transform(img).unsqueeze(0).to(mock_predictor.device)
    
    assert tensor.shape == (1, 3, 224, 224)
    with torch.no_grad():
        out = mock_predictor.model(tensor)
    assert out is not None

def test_evaluate_gate_thresholds():
    metrics = {
        "F1": 0.85,
        "Recall": 0.95,
        "Accuracy": 0.90,
        "Latency": 1.5, # Less than 3.0
    }
    # Should pass since F1 is better than dummy_f1 (0.80) and other conditions are met
    status = evaluate_gate(metrics, 0.80)
    assert status == "PASSED"
    
    # Test failure case (Latency > 3.0)
    failed_metrics = {
        "F1": 0.85,
        "Recall": 0.95,
        "Accuracy": 0.90,
        "Latency": 3.5,
    }
    status = evaluate_gate(failed_metrics, 0.80)
    assert status == "FAIL (Latency)"
    
    # Test failure case (Below Baseline)
    failed_baseline = {
        "F1": 0.75,
        "Recall": 0.95,
        "Accuracy": 0.90,
        "Latency": 1.5,
    }
    status = evaluate_gate(failed_baseline, 0.80)
    assert status == "FAIL (Below Baseline)"
