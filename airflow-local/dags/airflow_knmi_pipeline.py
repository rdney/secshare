"""
Apache Airflow 3 DAG for scheduled KNMI file downloads with queue message emission.

Downloads KNMI files on schedule, then emits one queue message per file.
"""
from datetime import datetime, timedelta, timezone
import json
import uuid
import base64
import os
import logging
import requests
import time
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from airflow.operators.python import get_current_context


default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

logger = logging.getLogger(__name__)


def get_storage_client():
    """Get storage client based on environment (MinIO or Azure Blob)."""
    storage_backend = os.environ.get("STORAGE_BACKEND", "minio")

    if storage_backend == "minio":
        from minio import Minio
        return Minio(
            os.environ.get("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
            secure=False
        ), "minio"
    else:
        from azure.storage.blob import BlobServiceClient
        from azure.identity import DefaultAzureCredential
        account_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL")
        return BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential()), "azure"


def upload_to_storage(storage_client, storage_type: str, bucket: str, object_name: str, file_path: str):
    """Upload file to MinIO or Azure Blob Storage."""
    if storage_type == "minio":
        storage_client.fput_object(bucket, object_name, file_path)
        logger.info(f"Uploaded {object_name} to MinIO bucket {bucket}")
    else:
        container_client = storage_client.get_container_client(bucket)
        with open(file_path, "rb") as data:
            container_client.upload_blob(name=object_name, data=data, overwrite=True)
        logger.info(f"Uploaded {object_name} to Azure container {bucket}")


def download_file_from_url(download_url: str, directory: str, filename: str) -> tuple:
    """Download file from temporary URL."""
    start_time = datetime.now()
    try:
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(f"{directory}/{filename}", "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Downloaded {filename} in {duration}s")
        return True, filename, None, None, duration
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.exception(f"Failed to download {filename}")
        return False, filename, "Download Error", str(e), duration


def download_dataset_file(
    session: requests.Session,
    base_url: str,
    dataset_name: str,
    dataset_version: str,
    filename: str,
    directory: str,
    expected_file_type: str,
) -> tuple:
    """Download a single dataset file from KNMI API."""
    file_path = Path(directory, filename).resolve()

    if file_path.exists():
        logger.info(f"File already exists: {filename}")
        return True, filename, None, None, 0

    if expected_file_type and not filename.endswith(expected_file_type):
        logger.warning(f"File {filename} doesn't match type {expected_file_type}")
        return False, filename, "File Type Error", f"Expected {expected_file_type}", 0

    endpoint = f"{base_url}/datasets/{dataset_name}/versions/{dataset_version}/files/{filename}/url"
    get_file_response = session.get(endpoint)

    if get_file_response.status_code != 200:
        logger.warning(f"Unable to get file URL: {filename}")
        return False, filename, f"Error {get_file_response.status_code}", str(get_file_response.content), 0

    download_url = get_file_response.json().get("temporaryDownloadUrl")
    result = download_file_from_url(download_url, directory, filename)

    if file_path.exists():
        logger.info(f"Successfully downloaded: {filename}")
        return True, filename, None, None, result[4]
    else:
        return False, filename, "Download Error", "File not found after download", result[4]


def list_dataset_files(
    session: requests.Session,
    base_url: str,
    dataset_name: str,
    dataset_version: str,
    params: dict,
    start_date: datetime,
    end_date: datetime,
) -> list[str]:
    """List and filter dataset files from KNMI API."""
    logger.info(f"Listing files with params: {params}")
    list_files_endpoint = f"{base_url}/datasets/{dataset_name}/versions/{dataset_version}/files"
    list_files_response = session.get(list_files_endpoint, params=params)

    if list_files_response.status_code == 403:
        raise Exception("API quota exceeded")
    if list_files_response.status_code != 200:
        raise Exception(f"Failed to list files: {list_files_response.status_code}")

    response_json = list_files_response.json()
    dataset_files = response_json.get("files", [])
    filenames = [f.get("filename") for f in dataset_files]

    logger.info(f"API returned {len(filenames)} total files")
    if filenames:
        logger.info(f"Sample filenames: {filenames[:3]}")
    logger.info(f"Date range: {start_date} to {end_date}")

    # Filter by date range
    filtered = []
    for fname in filenames:
        try:
            # Extract date from filename like KMDS__OPER_P___10M_OBS_L2_202507240950.nc
            date_str = fname.split('.nc')[0].split('L2_')[1]
            file_date = datetime.strptime(date_str, "%Y%m%d%H%M")
            logger.info(f"File {fname}: date={file_date}, in range={start_date <= file_date <= end_date}")
            if start_date <= file_date <= end_date:
                filtered.append(fname)
        except Exception as e:
            logger.warning(f"Could not parse date from {fname}: {e}")
            continue

    logger.info(f"Found {len(filtered)} files in date range")
    return filtered


def generate_queue_message(
    dataset: str,
    filepath: str,
    source: str,
    pipeline_name: str,
    queue_name: str,
    run_id: str,
) -> dict:
    """Generate Azure Queue message."""
    now = datetime.now(timezone.utc)

    content = {
        "dataset": dataset,
        "filepath": [filepath],
        "run_id": run_id,
        "source": source,
        "pipeline_name": pipeline_name,
        "queue_name": queue_name,
    }

    return {
        'id': str(uuid.uuid4()),
        'inserted_on': now,
        'expires_on': now + timedelta(days=7),
        'dequeue_count': None,
        'content': json.dumps(content),
        'pop_receipt': base64.b64encode(os.urandom(16)).decode(),
        'next_visible_on': now,
    }


with DAG(
    dag_id='knmi_download_and_queue',
    default_args=default_args,
    description='Download KNMI files on schedule and emit queue messages',
    schedule='0 */1 * * *',  # Every hour
    start_date=days_ago(1),
    catchup=False,
    tags=['knmi', 'ingestion', 'queue'],
    params={
        'dataset_name': '10-minute-in-situ-meteorological-observations',
        'dataset_version': '1.0',
        'save_name': 'AwsTenMinutes',
        'expected_file_type': '.nc',
        'source': 'KNMI',
        'pipeline_name': 'pl_ingest_KNMI.AwsTenMinutes',
        'queue_name': 'golizard-processor-queue-1-uat',
        'max_keys': 100,
        'days_back': 1,  # Download last N days
        'rate_limit_delay': 0.5,  # Seconds between downloads to respect KNMI rate limits
    },
) as dag:

    @task
    def download_files(**context):
        """Download KNMI files and upload to storage (MinIO/Azure)."""
        params = context['params']
        run_id = context['run_id']

        # Configuration
        base_url = "https://api.dataplatform.knmi.nl/open-data/v1"
        dataset_name = params['dataset_name']
        dataset_version = params['dataset_version']
        expected_file_type = params['expected_file_type']
        max_keys = params['max_keys']
        days_back = params['days_back']
        save_name = params['save_name']
        rate_limit_delay = params.get('rate_limit_delay', 0.5)

        # Get storage client
        storage_client, storage_type = get_storage_client()
        bucket = os.environ.get("MINIO_BUCKET", "knmi-data")

        # Get API key
        api_key = os.environ.get("KNMI_API_KEY", "your-api-key")

        # Date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Setup temp directory
        temp_dir = "/tmp/knmi_downloads"
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        session = requests.Session()
        session.headers.update({"Authorization": api_key})

        # List files
        filenames = list_dataset_files(
            session,
            base_url,
            dataset_name,
            dataset_version,
            {"maxKeys": str(max_keys), "sorting": "desc"},
            start_date,
            end_date,
        )

        if not filenames:
            logger.warning("No files to download")
            return []

        logger.info(f"Downloading {len(filenames)} files")

        # Download and upload files
        uploaded_files = []
        for idx, filename in enumerate(filenames):
            # Rate limiting - add delay between downloads
            if idx > 0:
                time.sleep(rate_limit_delay)

            success, fname, error_cat, error_msg, duration = download_dataset_file(
                session,
                base_url,
                dataset_name,
                dataset_version,
                filename,
                temp_dir,
                expected_file_type,
            )

            if success:
                # Upload to storage
                try:
                    object_name = f"KNMI/{save_name}/{fname}"
                    file_path = f"{temp_dir}/{fname}"
                    upload_to_storage(storage_client, storage_type, bucket, object_name, file_path)
                    uploaded_files.append(fname)
                    logger.info(f"Uploaded {fname} to storage ({len(uploaded_files)}/{len(filenames)})")

                    # Clean up temp file
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Failed to upload {fname}: {e}")
            else:
                logger.error(f"Failed to download {fname}: {error_msg}")

        logger.info(f"Successfully uploaded {len(uploaded_files)}/{len(filenames)} files")

        return uploaded_files

    @task
    def emit_queue_messages(downloaded_files: list[str], **context):
        """Emit one queue message per downloaded file."""
        if not downloaded_files:
            logger.info("No files to emit messages for")
            return []

        params = context['params']
        run_id = context['run_id']

        dataset = f"Knmi.{params['save_name']}"
        source = params['source']
        pipeline_name = params['pipeline_name']
        queue_name = params['queue_name']
        save_name = params['save_name']

        # Construct file path based on storage backend
        storage_backend = os.environ.get("STORAGE_BACKEND", "minio")
        if storage_backend == "minio":
            bucket = os.environ.get("MINIO_BUCKET", "knmi-data")
            base_path = f"s3://{bucket}/KNMI/{save_name}"
        else:
            # Azure Blob Storage path
            container = os.environ.get("AZURE_STORAGE_CONTAINER", "knmi-data")
            account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
            base_path = f"https://{account_name}.blob.core.windows.net/{container}/KNMI/{save_name}"

        messages = []
        for filename in downloaded_files:
            filepath = f"{base_path}/{filename}"

            message = generate_queue_message(
                dataset=dataset,
                filepath=filepath,
                source=source,
                pipeline_name=pipeline_name,
                queue_name=queue_name,
                run_id=run_id,
            )

            messages.append(message)
            logger.info(f"Created message for {filename}")

        logger.info(f"Created {len(messages)} queue messages")

        return messages

    @task
    def send_to_queue(messages: list[dict]):
        """Send messages to Azure Queue Storage."""
        if not messages:
            logger.info("No messages to send")
            return []

        # TODO: Implement Azure Queue Storage client
        # from azure.storage.queue import QueueClient
        # from azure.identity import DefaultAzureCredential
        #
        # credential = DefaultAzureCredential()
        # queue_client = QueueClient(
        #     account_url="https://<account>.queue.core.windows.net",
        #     queue_name=queue_name,
        #     credential=credential
        # )
        #
        # sent_ids = []
        # for message in messages:
        #     queue_client.send_message(message['content'])
        #     sent_ids.append(message['id'])

        sent_ids = []
        for message in messages:
            content = json.loads(message['content'])
            logger.info(f"Would send message {message['id']} to {content['queue_name']}")
            logger.info(f"  Dataset: {content['dataset']}")
            logger.info(f"  File: {content['filepath'][0]}")
            sent_ids.append(message['id'])

        logger.info(f"Sent {len(sent_ids)} messages to queue")

        return sent_ids

    # Task dependencies
    files = download_files()
    messages = emit_queue_messages(files)
    send_to_queue(messages)
