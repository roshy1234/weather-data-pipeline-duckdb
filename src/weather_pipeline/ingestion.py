import json
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

LOCATIONS = [
    {"location_id": "kochi", "city": "Kochi", "latitude": 9.9312, "longitude": 76.2673},
    {"location_id": "bengaluru", "city": "Bengaluru", "latitude": 12.9716, "longitude": 77.5946},
    {"location_id": "delhi", "city": "Delhi", "latitude": 28.6139, "longitude": 77.2090}
]

def fetch_weather(location: dict) -> dict:
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"],
        "forecast_days": 1,
        "timezone": "Asia/Kolkata",
    }
    response = requests.get(API_URL, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if "hourly" not in payload or "time" not in payload["hourly"]:
        raise ValueError("API response missing hourly data")
    return payload

def save_raw_batch(payload: dict, location: dict, batch_id: str, ingested_at: datetime) -> Path:
    batch = {
        "batch_id": batch_id,
        "ingested_at_utc": ingested_at.isoformat(),
        "source": "Open-Meteo",
        "location": location,
        "response": payload,
    }
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_file = RAW_DATA_DIR / f"weather_batch_{batch_id}.json"
    output_file.write_text(json.dumps(batch, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_file