# Golizard Containerapp (ACA)

This is the ingestion tool for running GoLizard in an Azure Container App or Azure Function.

## Local Development

To run locally, start Docker:

```bash
docker compose up
```

This will start a mock Lizard server (mocks v4) and some Fabric SQL mock servers.

## Azure Container App Deployment

### Prerequisites

- Azure subscription
- Azure CLI installed and authenticated
- Docker Desktop with buildx capability
- GitHub repository (for GitHub Actions deployment)

### Deployment Options

#### Option 1: Manual Deployment

1. Update the environment variables in `azure.env` with your actual values
2. Run the deployment script:

```bash
./deploy-to-azure.sh
```

This script will:
- Create a resource group if it doesn't exist
- Create an Azure Container Registry 
- Build and push a Docker image using Dockerfile.azure
- Create a managed identity for the Container App
- Create/update the Container App with all environment variables
- Assign necessary roles to access the Azure Data Lake Storage

#### Option 2: GitHub Actions Deployment

1. Add the following secrets to your GitHub repository:
   - `AZURE_CREDENTIALS`: Azure service principal credentials
   - `ACR_USERNAME`: Azure Container Registry username
   - `ACR_PASSWORD`: Azure Container Registry password
   - All environment variables from `azure.env`

2. Push changes to the main branch to trigger the deployment workflow, or manually trigger it from the Actions tab.

### Database Setup

To set up the PostgreSQL database in Azure:

1. Update the password in `setup-azure-db.sh`
2. Run the database setup script:

```bash
./setup-azure-db.sh
```

3. Update the database connection details in your Azure Container App environment variables

## ETL Tool Usage

The `etl_tool.py` script supports both local file paths and Azure Data Lake Storage paths.

### Using Local Files

```json
{
    "filepath": [
        [
            "KNMI_SYNOPS",
            "/data/KNMI_SYNOPS/decoded_synops_20250331203638.txt"
        ]
    ],
    "run_id": "local-run-id",
    "originating_pl_run_id": "local-pipeline-id"
}
```

### Using Azure Data Lake Storage Files

```json
{
    "filepath": [
        [
            "KNMI_SYNOPS",
            "lakehouse://knmidata/knmi_synops/decoded_synops_20250331203638.txt"
        ]
    ],
    "run_id": "lakehouse-test-run",
    "originating_pl_run_id": "lakehouse-test"
}
```

The `lakehouse://` URI scheme is used to reference files in the Data Lake. The format is:
`lakehouse://container/path/to/file.txt`

### Sending Logs to Lakehouse

To enable sending logs to the lakehouse, use the `--send-logs` flag:

```bash
python etl_tool.py '{"filepath":[["KNMI_SYNOPS","/path/to/file.txt"]]}' --send-logs
```

## Azure Data Lake Integration

The ETL tool has been enhanced to read files directly from Azure Data Lake Storage, which is used by the Fabric Lakehouse. This integration:

1. Uses managed identity authentication when running in Azure
2. Falls back to DefaultAzureCredential for local development
3. Downloads files to temporary storage before processing
4. Cleans up temporary files after processing
5. Maintains backward compatibility with local file paths

### Configuration

Set the following environment variables in `azure.env`:

```
LAKEHOUSE_STORAGE_ACCOUNT=yourstorageaccount
LAKEHOUSE_CONTAINER=knmidata
```

### Authentication

- **In Azure**: The Container App uses its managed identity (created during deployment)
- **Local Development**: Use Azure CLI (`az login`) to authenticate via DefaultAzureCredential

## Lizard Mock Server

The Lizard server mocks API v4 endpoints:

```
/timeseries/
/timeseries/events/
/locations/
/organisations/
/rasters/
/rastersources/{uuid}/data/
```

It mocks both POST and GET where appropriate.

As you can see, rastersources requires a valid UUID. This is controlled by an env var. See `env.example`. You can also insert a dummy into the rastersources table if you prefer.

## Database

At the moment, there is also a real PostgreSQL metadata database involved.

This database is completely empty upon creation. Flyway is used to migrate it.
You can test your data migrations there.

## Environment Variables

See `env.example` and `azure.env` for a complete list of required environment variables.

Key variables include:

- `GOLIZARD_VERSION` - Version number of golizard
- `LIZARD_BASE_URL` - Base URL for the Lizard API
- `FABRIC_SQL_ENDPOINT` - Endpoint for the Fabric SQL service
- `LAKEHOUSE_STORAGE_ACCOUNT` - Azure Storage account for the lakehouse
- `LAKEHOUSE_CONTAINER` - Default container for the lakehouse files

## Bypassing Hardcoded LIZARD_BASE_URL

GoLizard hardcodes the base URL (lizard.twin.io/api/v4) in global_config.py.

The `entrypoint.sh` patches global_config.py to accept the mock base URL for local and CI/CD use.

## Testing

For rapid testing, have a look at `trigger.sh`. It runs ETL jobs with commands like:

```bash
run_etl_job "run-${TIMESTAMP}-iris-unvalidated" "$(cat <<EOF
{
  "filepath": [
    ["KNMI_IRIS_UNVALIDATED", "/data/KNMI_IRIS_UNVALIDATED/regensom_2025042618.txt"],
    ["KNMI_IRIS_UNVALIDATED", "/data/KNMI_IRIS_UNVALIDATED/regensom_2025042818.txt"],
    ["KNMI_IRIS_UNVALIDATED", "/data/KNMI_IRIS_UNVALIDATED/regensom_2025042918.txt"]
  ],
  "run_id": "run-${TIMESTAMP}-iris-unvalidated",
  "originating_pl_run_id": "manual-trigger"
}
EOF
)"
```

The `run_etl_job` is a shell function that calls etl_tool.py which runs the ETL process and stores logs in the `./logs` directory.

## Docker Images

- **Dockerfile** - Original Docker image for local development
- **Dockerfile.azure** - Specialized Docker image for Azure Container App deployment
  - Uses osgeo/gdal base image
  - Supports linux/amd64 platform
  - Includes Azure SDK dependencies
  - Properly configures timezone to avoid interactive prompts

## Supported Data Sources

The application supports processing the following data sources:

- KNMI AWS
- KNMI SYNOPS
- KNMI IRIS (Validated and Unvalidated)
- KNMI Rain Gauge
- KNMI Weather Warnings
- KNMI Radar (Uncorrected)
- KNMI RIC
- Harmonie43 Transformer
- HarmonieKEPS Transformer

## Dependencies

For Azure deployment, additional dependencies are required:
- azure-identity
- azure-storage-file-datalake

These are included in the `requirements-azure.txt` file.

## TODO

- Terraform# wiwb-api
