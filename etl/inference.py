import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import torch
from torchvision import transforms
from PIL import Image

from etl.config.helpers import PROJECT_ROOT
from ml_pipeline.utils import resolve_image_path

logger = logging.getLogger(__name__)


class PlantDiseasePredictor:
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_version = self.model_path.stem
        self.model = None
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

    def load_model(self):
        if self.model is None:
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model checkpoint not found: {self.model_path}"
                )
            logger.info(f"Loading TorchScript model from {self.model_path}")
            self.model = torch.jit.load(str(self.model_path), map_location=self.device)
            self.model.eval()

    def run_inference(self, conn: sqlite3.Connection) -> dict[str, int]:
        """Runs inference on observations that lack predictions."""
        # Query for unpredicted records
        query = """
            SELECT o.id as observation_id, o.image_url, o.source, o.external_id
            FROM observations o
            LEFT JOIN predictions p ON o.id = p.observation_id
            WHERE p.id IS NULL
        """
        df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.info("[ INFERENCE ] No new observations to predict.")
            return {"predicted": 0}

        logger.info(f"[ INFERENCE ] Found {len(df)} unpredicted observations.")

        self.load_model()

        # Resolve paths
        df["local_path"] = df.apply(resolve_image_path, axis=1)
        valid_df = df[df["local_path"].notnull()].copy()

        if valid_df.empty:
            logger.warning(
                "[ INFERENCE ] No resolvable images found for unpredicted observations."
            )
            return {"predicted": 0}

        logger.info(f"[ INFERENCE ] Running predictions on {len(valid_df)} images...")

        batch_size = 500
        total_predicted = 0

        for i in range(0, len(valid_df), batch_size):
            chunk = valid_df.iloc[i : i + batch_size].copy()
            predictions = []
            confidences = []

            with torch.no_grad():
                for _, row in chunk.iterrows():
                    try:
                        img = Image.open(row["local_path"]).convert("RGB")
                        tensor = self.transform(img).unsqueeze(0).to(self.device)  # pyright: ignore[reportAttributeAccessIssue]
                        if self.model is None:
                            raise Exception("Model not loaded")
                        out = self.model(tensor)
                        prob = torch.sigmoid(out).item()
                        pred_class = 1 if prob > 0.5 else 0

                        predictions.append(pred_class)
                        confidences.append(prob)
                    except Exception as e:
                        logger.error(
                            f"Failed to predict image {row['local_path']}: {e}"
                        )
                        predictions.append(-1)
                        confidences.append(0.0)

            chunk["predicted_is_diseased"] = predictions
            chunk["confidence"] = confidences
            chunk["model_version"] = self.model_version
            chunk["predicted_at"] = datetime.now(timezone.utc).isoformat()

            success_chunk = chunk[chunk["predicted_is_diseased"] != -1].copy()
            if not success_chunk.empty:
                cols_to_load = [
                    "observation_id",
                    "predicted_is_diseased",
                    "confidence",
                    "model_version",
                    "predicted_at",
                ]
                success_chunk[cols_to_load].to_sql(
                    "predictions", conn, if_exists="append", index=False
                )
                total_predicted += len(success_chunk)
                logger.info(
                    f"[ INFERENCE ] Progress: {total_predicted}/{len(valid_df)} saved."
                )

        logger.info(f"[ INFERENCE ] Finished. Total saved: {total_predicted}")
        return {"predicted": total_predicted}


def run_inference_stage(config) -> dict[str, int]:
    db_path = PROJECT_ROOT / config.load.target_path
    model_path = (
        PROJECT_ROOT / "data" / "checkpoints" / "mobilenetv2_standard_2500_scripted.pt"
    )

    logger.info(f"[ INFERENCE ] Connecting to {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        predictor = PlantDiseasePredictor(model_path)
        stats = predictor.run_inference(conn)
        return stats
    finally:
        conn.close()
