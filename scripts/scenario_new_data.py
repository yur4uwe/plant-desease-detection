"""
Scenario 1: Prediction on new data (Real-time single/small batch simulation)
Simulates receiving a new observation, inserting it into the database,
and running the inference pipeline to get a prediction.
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone

from etl.inference import PlantDiseasePredictor
from etl.config.helpers import PROJECT_ROOT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("scenario_new_data")

def main():
    db_path = PROJECT_ROOT / "data" / "processed" / "observations.db"
    model_path = PROJECT_ROOT / "data" / "checkpoints" / "model.pt"

    if not model_path.exists():
        logger.error(f"Model not found at {model_path}. Please train or export a model first.")
        return

    logger.info("Connecting to database...")
    conn = sqlite3.connect(db_path)
    
    # Simulate a new incoming observation
    # We will pick an existing valid local path but give it a new ID to simulate fresh data
    cursor = conn.cursor()
    
    # Fetch a random valid image path
    cursor.execute("SELECT image_url, source FROM observations WHERE image_url IS NOT NULL LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
         logger.error("No valid observations found in DB to mock new data.")
         return
         
    mock_url, mock_source = row
    
    mock_external_id = f"mock_{int(datetime.now().timestamp())}"
    current_time = datetime.now(timezone.utc).isoformat()
    
    logger.info("1. Simulating arrival of new data...")
    cursor.execute(
        '''
        INSERT INTO observations (external_id, source, image_url, quality_score, has_nulls, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (mock_external_id, mock_source, mock_url, 1.0, 0, current_time, current_time)
    )
    conn.commit()
    logger.info(f"Inserted new observation with external_id: {mock_external_id}")
    
    logger.info("2. Running inference pipeline on new data...")
    predictor = PlantDiseasePredictor(model_path)
    result = predictor.run_inference(conn)
    
    logger.info(f"3. Inference completed. Result: {result}")
    
    # Check what was predicted
    cursor.execute(
        '''
        SELECT p.prediction_class, p.confidence 
        FROM predictions p 
        JOIN observations o ON p.observation_id = o.id
        WHERE o.external_id = ?
        ''',
        (mock_external_id,)
    )
    pred_row = cursor.fetchone()
    if pred_row:
        logger.info(f"Prediction for new data: Class={pred_row[0]}, Confidence={pred_row[1]:.4f}")
    else:
        logger.warning("No prediction found for the new data.")
        
    conn.close()

if __name__ == "__main__":
    main()
