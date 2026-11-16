import json
import os
import shutil
from pathlib import Path

import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

def load_all_to_motherduck(file_paths: list[Path]) -> None:
    if not file_paths:
        return

    all_records = []
    
    # Read and parse all files
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            batch = json.load(f)
            
        payload = batch["response"]
        hourly = payload["hourly"]
        
        df = pd.DataFrame({
            "batch_id": batch["batch_id"],
            "ingested_at": pd.to_datetime(batch["ingested_at_utc"]),
            "location_id": batch["location"]["location_id"],
            "forecast_time": pd.to_datetime(hourly["time"]),
            "temperature_2m": hourly["temperature_2m"],
            "relative_humidity_2m": hourly["relative_humidity_2m"],
            "precipitation": hourly["precipitation"],
            "wind_speed_10m": hourly["wind_speed_10m"]
        })
        all_records.append(df)

    # Merge into a single master DataFrame
    combined_df = pd.concat(all_records, ignore_index=True)

    # Open ONE connection and execute ONE bulk insert
    con = duckdb.connect(f'md:weather_warehouse?motherduck_token={MOTHERDUCK_TOKEN}')
    try:
        con.register('temp_df', combined_df)
        con.execute("INSERT INTO weather_raw.raw_weather_forecasts SELECT * FROM temp_df")
    finally:
        con.close()

    # Archive files only after successful database insertion
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for file_path in file_paths:
        destination = PROCESSED_DATA_DIR / file_path.name
        shutil.move(str(file_path), str(destination))
