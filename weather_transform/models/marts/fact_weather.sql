SELECT 
    -- Generate a unique Surrogate Key natively in DuckDB
    md5(location_id || forecast_time::VARCHAR) AS weather_fact_id,
    
    location_id,
    forecast_time,
    temperature_celsius,
    humidity_percentage,
    precipitation_mm,
    wind_speed_kmh
FROM {{ ref('stg_hourly_weather') }}