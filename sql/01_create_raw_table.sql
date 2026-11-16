CREATE SCHEMA IF NOT EXISTS weather_raw;

-- 2. Create the table using PostgreSQL data types. 
CREATE TABLE IF NOT EXISTS weather_raw.raw_weather_forecasts (
    batch_id VARCHAR,
    ingested_at TIMESTAMP,
    location_id VARCHAR,
    forecast_time TIMESTAMP,
    temperature_2m DOUBLE,
    relative_humidity_2m DOUBLE,
    precipitation DOUBLE,
    wind_speed_10m DOUBLE
);