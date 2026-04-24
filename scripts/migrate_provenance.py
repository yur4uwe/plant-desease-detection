import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    db_path = "etl/data/processed/observations.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        logger.info("Adding 'provenance' column to observations table...")
        cur.execute("ALTER TABLE observations ADD COLUMN provenance TEXT")
        
        logger.info("Backfilling existing records with 'Field' provenance...")
        cur.execute("UPDATE observations SET provenance = 'Field' WHERE provenance IS NULL")
        
        conn.commit()
        logger.info("Migration successful.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("Column 'provenance' already exists. Skipping.")
        else:
            logger.error(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
