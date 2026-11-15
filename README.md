# Weather Data Pipeline & Analytics Hub

An end-to-end, containerized ELT (Extract, Load, Transform) data engineering pipeline that ingests real-time meteorological data for **Kochi, Bengaluru, and Delhi**, transforms it into an analytical Star Schema, and visualizes key climate trends across interactive dashboards.

## Architecture & Tech Stack

* **Orchestration:** **Prefect Cloud** (with a custom containerized Prefect Worker) for workflow scheduling, task dependency management, retry logic, and pipeline observability.

* **Data Warehouse:** **ClickHouse** serving as a high-performance, columnar OLAP database.

* **Transformation:** **dbt (Data Build Tool)** for transforming raw tables from clickhouse into a clean, analytics-ready Star Schema inside the `weather_warehouse_analytics` database.

* **Visualization (Dual Layer):**

  * **Streamlit:** Interactive Python web application (`Weather Analytics Hub`) deployed on Streamlit Community Cloud for exploring temperature, humidity, precipitation, and wind speed trends.

  * **Grafana OSS:** Lightweight operational dashboard connected via the official ClickHouse plugin for real-time monitoring.

* **Containerization & CI/CD:** **Docker & Docker Compose** for local orchestration, paired with **GitHub Actions** for automated linting, testing, and Continuous Delivery (CD) to Docker Hub.

## Data Model (Star Schema)

The raw weather data is transformed via dbt into a dimensional Star Schema located in the `weather_warehouse_analytics` database:

### 1. Fact Table: `fact_weather`

Stores the granular time-series meteorological measurements.

* `weather_fact_id`(Primary Key)

* `location_id` (Foreign Key)

* `forecast_time` (Timestamp)

* `temperature_celsius` (Float)

* `humidity_percentage` (Float)

* `precipitation_mm` (Float)

* `wind_speed_kmh` (Float)

### 2. Dimension Table: `dim_location`

Stores static geographical metadata for the tracked cities.

* `location_id` (Primary Key)

* `city_name` (String - e.g., Kochi, Bengaluru, Delhi)

* `latitude` (Float)

* `longitude` (Float)

## Performance & Memory Optimizations

1. **Grafana OSS Footprint:** Uses the stripped-down `grafana-oss` image capped with `GOMEMLIMIT` and strict Docker deploy resource limits.

2. **Zero-Leak Streamlit Caching:** Separates database connection caching (`@st.cache_resource`) from query result caching (`@st.cache_data(ttl=300)`) and uses native Altair line charts (`st.line_chart`) to prevent memory leaks and heavy library import penalties.

## Local Setup & Installation

### Prerequisites

* Docker & Docker Compose (WSL2 backend recommended if on Windows)

* A Prefect Cloud account & API Key

* Weather API credentials

### 1. Clone the Repository

```
git clone https://github.com/roshy1234/weather-data-pipeline.git
cd weather-data-pipeline


```

### 2. Configure Environment Variables

Create a `.env` file in the root directory of the project:

```
# ClickHouse Configuration
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your_secure_password

# Prefect Configuration
PREFECT_API_KEY=your_prefect_cloud_api_key
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/.../workspaces/...

# Weather API URL
WEATHER_API_URL="https://api.open-meteo.com/v1/forecast"


```

### 3. Launch the Stack

Spin up the containers in detached mode:

```
docker compose up -d --build

View the full container setup in [`compose.yml`](./compose.yml).
```

### 4. Monitoring and Observability

* **Grafana UI:** Accessible at `http://localhost:3000`

* **Streamlit UI (Local):** Accessible at `http://localhost:8501`

## CI/CD & Cloud Deployment

### Continuous Delivery (GitHub Actions to Docker Hub)

A unified GitHub Actions workflow (`.github/workflows/ci-cd.yml`) automatically runs code quality checks on every push to `main`. Once tests pass, it builds and pushes the custom application images to two separate public Docker Hub repositories:

* `roshyjamz/weather-worker:latest` (Contains the Prefect flows, ingestion, loader, and dbt scripts)

* `roshyjamz/weather-dashboard:latest` (Contains the Streamlit application)