# Local Airflow Setup for WIWB

Local Airflow environment for KNMI data ingestion pipelines.

## Prerequisites

- Docker Desktop running
- Docker Compose
- PostgreSQL running locally on port 5432 with database `airflow` and user `airflow`

## Structure

```
airflow-local/
├── dags/
│   ├── knmi_dag_factory.py        # Factory for creating KNMI dataset DAGs
│   ├── airflow_knmi_pipeline.py   # Legacy single dataset DAG
│   └── airflow_message_emitter.py # Message emitter DAG
├── logs/              # Airflow logs
├── plugins/           # Custom Airflow plugins
├── config/            # Configuration files
├── docker-compose.yml # Docker Compose configuration
├── .env               # Environment variables
└── README.md
```

## Setup

1. **Ensure PostgreSQL is running locally:**
   ```bash
   psql -d airflow -c "ALTER DATABASE airflow OWNER TO airflow;"
   psql -d airflow -c "ALTER SCHEMA public OWNER TO airflow;"
   ```

2. **Start Docker Desktop**

3. **Start all services:**
   ```bash
   cd /Users/rodney/Projects/airflow-local
   docker compose up -d
   ```

4. **Access services:**
   - Airflow UI: http://localhost:8080 (username: `airflow`, password: `airflow`)
   - MinIO Console: http://localhost:9001 (username: `minioadmin`, password: `minioadmin`)
   - MinIO API: http://localhost:9000

## Adding a New DAG

Edit `dags/knmi_dag_factory.py`, add at bottom:

```python
my_dag = create_knmi_dag(
    dag_id='unique_id',
    dataset_name='dataset-from-knmi',
    dataset_version='1.0',
    save_name='SaveName',
    schedule='0 */1 * * *',
    expected_file_type='.nc',
    max_keys=100,
    days_back=1,
    rate_limit_delay=0.5,
    tags=['knmi'],
)
```

Restart: `docker compose restart airflow-scheduler`

Parameters:
- `dag_id`: unique identifier
- `dataset_name`: from KNMI Data Platform
- `dataset_version`: usually `1.0`
- `save_name`: storage path name
- `schedule`: cron expression
- `expected_file_type`: `.nc` or `.h5`
- `max_keys`: files per run
- `days_back`: lookback window
- `rate_limit_delay`: seconds between downloads
- `tags`: list of strings

## DAG Workflow

Each factory-created DAG has 3 tasks:

1. **download_files** - Downloads files from KNMI API, uploads to MinIO/Azure
2. **emit_queue_messages** - Creates one queue message per downloaded file
3. **send_to_queue** - Sends messages to Azure Queue Storage (currently placeholder)

## Storage

- **Local (development)**: Uses MinIO (S3-compatible) at `minio:9000`
- **Production**: Uses Azure Blob Storage

Storage backend is controlled by `STORAGE_BACKEND` env var in `.env`:
```bash
STORAGE_BACKEND=minio  # or 'azure' for production
```

## Environment Variables

Edit `.env` to configure:

```bash
# Airflow
AIRFLOW_UID=50000
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

# Python dependencies
_PIP_ADDITIONAL_REQUIREMENTS=azure-storage-queue==12.11.0 azure-identity==1.19.0 minio==7.2.11

# KNMI API
KNMI_API_KEY=your-api-key-here

# Storage
STORAGE_BACKEND=minio
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=knmi-data
```

## Common Commands

### View logs
```bash
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-webserver
```

### List DAGs
```bash
docker compose exec airflow-scheduler airflow dags list | grep knmi
```

### Pause/Unpause DAG
```bash
docker compose exec airflow-scheduler airflow dags pause knmi_10min_observations
docker compose exec airflow-scheduler airflow dags unpause knmi_radar_rtcor_5m
```

### Trigger DAG manually
```bash
docker compose exec airflow-scheduler airflow dags trigger knmi_radar_rtcor_5m
```

### Test DAG
```bash
docker compose exec airflow-scheduler airflow dags test knmi_radar_rtcor_5m
```

## Stop Services

```bash
docker compose down
```

## Clean Up (remove all data)

```bash
docker compose down -v
```

## Troubleshooting

### DAGs don't appear
- Check `logs/scheduler/` for errors
- Verify DAG file syntax: `docker compose exec airflow-scheduler airflow dags list`
- Restart scheduler: `docker compose restart airflow-scheduler`

### Database connection errors
Ensure local PostgreSQL is running and accessible:
```bash
psql -d airflow -c "SELECT version();"
```

### Rate limit errors from KNMI API
Increase `rate_limit_delay` parameter in your DAG configuration:
```python
rate_limit_delay=1.0  # Increase to 1 second between downloads
```

### Files not appearing in MinIO
Check MinIO console at http://localhost:9001 and verify:
- Bucket `knmi-data` exists
- Files are in `KNMI/<save_name>/` directory
