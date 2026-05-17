import torch
import torchvision.models as models
from pathlib import Path

def export_model():
    model_path = Path("data/checkpoints/mobilenetv2_standard_2500.pt")
    out_path = Path("data/checkpoints/mobilenetv2_standard_2500_scripted.pt")
    
    # Load model structure
    model = models.mobilenet_v2()
    model.classifier[1] = torch.nn.Linear(model.last_channel, 1)
    
    # Load weights
    try:
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        print("Loaded state_dict successfully")
    except Exception as e:
        print(f"Could not load state dict: {e}")
        # Maybe it's a full model?
        model = torch.load(model_path, map_location="cpu")
        
    model.eval()
    
    # Export to TorchScript
    scripted_model = torch.jit.script(model)
    scripted_model.save(out_path)
    print(f"Exported TorchScript model to {out_path}")

if __name__ == "__main__":
    export_model()
