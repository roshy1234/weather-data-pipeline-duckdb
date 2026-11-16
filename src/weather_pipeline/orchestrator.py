import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from ingestion import LOCATIONS, fetch_weather, save_raw_batch
from loader import load_all_to_motherduck
from prefect import flow, get_run_logger, task

# Use your specific copied path here!
DBT_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent / "weather_transform"

@task(retries=2, retry_delay_seconds=10)
def extract_task(location: dict) -> Path:
    logger = get_run_logger()
    ingested_at = datetime.now(UTC)
    batch_id = f"{location['location_id']}_{ingested_at.strftime('%Y%m%dT%H%M%S%fZ')}"
    
    logger.info(f"Extracting data for {location['city']}...")
    payload = fetch_weather(location)
    raw_file = save_raw_batch(payload, location, batch_id, ingested_at)
    
    return raw_file

@task
def load_task(file_paths: list[Path]):
    logger = get_run_logger()
    logger.info(f"Bulk loading {len(file_paths)} files to MotherDuck...")
    load_all_to_motherduck(file_paths)
    logger.info("Successfully loaded and archived all batches.")

@task
def dbt_run_task():
    logger = get_run_logger()
    logger.info("Executing dbt run...")
    result = subprocess.run(["dbt", "run"], cwd=DBT_PROJECT_DIR, capture_output=True, text=True)  # noqa: PLW1510
    if result.returncode != 0:
        logger.error(f"dbt run failed!\n{result.stderr}\n{result.stdout}")
        raise RuntimeError("dbt run failed")
    logger.info(f"dbt run completed:\n{result.stdout}")

@task
def dbt_test_task():
    logger = get_run_logger()
    logger.info("Executing dbt test...")
    result = subprocess.run(["dbt", "test"], cwd=DBT_PROJECT_DIR, capture_output=True, text=True)  # noqa: PLW1510
    if result.returncode != 0:
        logger.error(f"dbt test failed!\n{result.stderr}\n{result.stdout}")
        raise RuntimeError("dbt test failed")
    logger.info(f"dbt test completed:\n{result.stdout}")

@flow(name="End-to-End Weather Pipeline")
def main_flow():
    # Phase 1: Extract all APIs concurrently
    extract_futures = []
    for location in LOCATIONS:
        future = extract_task.submit(location)
        extract_futures.append(future)
        
    # Wait for all API calls to finish and collect the file paths into a LIST
    raw_file_paths = [future.result() for future in extract_futures]
    
    # Phase 2: Bulk load the entire LIST using a single connection
    load_task(raw_file_paths)
        
    # Phase 3 & 4: Transformation and Data Quality
    dbt_run_task()
    dbt_test_task()
    
    # Prevent telemetry drop on final task
    time.sleep(2)

if __name__ == "__main__":
    main_flow.serve(
        name="daily-weather-pipeline-duckdb",
        cron="0 12 * * *",  # Runs every day at 12:00 PM
        tags=["weather", "production", "motherduck"],
        description="End-to-end weather extraction, loading, and dbt transformation"
    )