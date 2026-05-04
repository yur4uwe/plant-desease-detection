import pandas as pd
import numpy as np
import datetime
import uuid
import os

def generate_synthetic_data(num_samples: int = 150, output_path: str = "data/syn_data_gen_tsar.csv"):
    """
    Generates synthetic data simulating observations, including normal data and deliberate anomalies
    such as out-of-range coordinates, extreme temperatures, and negative precipitation.
    """
    np.random.seed(42)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Base data generation within normal bounds based on docs/EDA.md
    data = {
        'id': np.arange(2000000, 2000000 + num_samples),
        'source': np.random.choice(['inaturalist', 'local_ccmt_ghana', 'yolo_mcdd_india'], num_samples, p=[0.5, 0.2, 0.3]),
        'external_id': [str(uuid.uuid4())[:8] for _ in range(num_samples)],
        'image_url': [f"https://synthetic-data.com/img_{i}.jpg" for i in range(num_samples)],
        'label': np.random.choice(['banana_yb_sigatoka', 'Tomato_septoria leaf spot', 'Healthy_Plant'], num_samples),
        'is_diseased': np.random.choice([0, 1], num_samples, p=[0.25, 0.75]),
        'latitude': np.random.uniform(-51.14, 67.28, num_samples),
        'longitude': np.random.uniform(-157.91, 175.85, num_samples),
        'observation_date': [
            (datetime.datetime(2024, 1, 1) + datetime.timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d')
            for _ in range(num_samples)
        ],
        'extracted_at': datetime.datetime.now(datetime.UTC).isoformat(),
        'loaded_at': datetime.datetime.now(datetime.UTC).isoformat(),
        'season': np.random.choice(['Spring', 'Summer', 'Autumn', 'Winter', np.nan], num_samples),
        'solar_status': np.random.choice(['Daylight', 'Night', np.nan], num_samples),
        'temperature': np.random.normal(14.26, 6.43, num_samples),
        'precipitation': np.abs(np.random.normal(1.81, 4.72, num_samples)),
        'provenance': np.random.choice(['Field', 'Laboratory'], num_samples, p=[0.9, 0.1])
    }
    
    df = pd.DataFrame(data)
    
    # Inject Anomalies (approx 15% of data)
    num_anomalies = int(num_samples * 0.15)
    anomaly_indices = np.random.choice(num_samples, num_anomalies, replace=False)
    
    # Split anomaly indices into 3 groups
    idx_group1 = anomaly_indices[:num_anomalies//3]
    idx_group2 = anomaly_indices[num_anomalies//3:2*num_anomalies//3]
    idx_group3 = anomaly_indices[2*num_anomalies//3:]
    
    # 1. Invalid coordinates (latitude > 90 or < -90)
    df.loc[idx_group1, 'latitude'] = np.random.uniform(95.0, 150.0, len(idx_group1))
    df.loc[idx_group1, 'longitude'] = np.random.uniform(190.0, 300.0, len(idx_group1))
    
    # 2. Extreme temperatures (e.g. 150 Celsius)
    df.loc[idx_group2, 'temperature'] = np.random.uniform(80.0, 150.0, len(idx_group2))
    
    # 3. Negative precipitation (impossible in reality)
    df.loc[idx_group3, 'precipitation'] = np.random.uniform(-50.0, -10.0, len(idx_group3))
    
    # Inject Duplicates (add 5 exact copies of random rows)
    duplicates = df.sample(5, random_state=1)
    df = pd.concat([df, duplicates], ignore_index=True)
    
    # Inject Missing Values in Numerical columns (to be imputed)
    missing_indices = np.random.choice(num_samples, 10, replace=False)
    df.loc[missing_indices, 'temperature'] = np.nan
    df.loc[missing_indices, 'precipitation'] = np.nan
    
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {len(df)} synthetic records with anomalies and saved to {output_path}")

if __name__ == "__main__":
    generate_synthetic_data()
