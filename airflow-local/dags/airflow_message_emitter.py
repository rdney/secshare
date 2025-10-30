"""
Apache Airflow 3 DAG for processing KNMI ingestion messages and emitting to queue.

Integrates with nb_full_ingestion_KNMI.py which downloads KNMI files
and creates messages for queue processing.
"""
from datetime import datetime, timedelta, timezone
import json
import uuid
import base64
import os

from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
from airflow.operators.python import get_current_context


default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def generate_queue_message(
    dataset: str,
    filepath: list[str],
    source: str,
    pipeline_name: str,
    queue_name: str,
    run_id: str = None,
) -> dict:
    """
    Generate Azure Queue message with required fields.

    Args:
        dataset: Dataset identifier (e.g., "Knmi.AwsTenMinutes")
        filepath: List of file paths
        source: Data source (e.g., "KNMI")
        pipeline_name: Name of the pipeline
        queue_name: Target queue name
        run_id: Optional run ID, generated if not provided

    Returns:
        Dictionary with Azure Queue message structure
    """
    now = datetime.now(timezone.utc)

    content = {
        "dataset": dataset,
        "filepath": filepath,
        "run_id": run_id or str(uuid.uuid4()),
        "source": source,
        "pipeline_name": pipeline_name,
        "queue_name": queue_name,
    }

    message = {
        'id': str(uuid.uuid4()),
        'inserted_on': now,
        'expires_on': now + timedelta(days=7),
        'dequeue_count': None,
        'content': json.dumps(content),
        'pop_receipt': base64.b64encode(b'AgAAAAMAAAAAAAAAcyXqoBs53AE=').decode(),
        'next_visible_on': now,
    }

    return message


with DAG(
    dag_id='knmi_ingestion_to_queue',
    default_args=default_args,
    description='Process KNMI ingestion output and emit queue messages',
    schedule=None,
    start_date=days_ago(1),
    catchup=False,
    tags=['knmi', 'queue', 'ingestion'],
    params={
        'dataset': 'Knmi.AwsTenMinutes',
        'source': 'KNMI',
        'pipeline_name': 'pl_ingest_KNMI.AwsTenMinutes',
        'queue_name': 'golizard-processor-queue-1-uat',
        'ingestion_output_path': '/tmp/nb_ingest_output.json',
    },
) as dag:

    @task
    def read_ingestion_output():
        """Read KNMI ingestion output from nb_full_ingestion_KNMI.py."""
        context = get_current_context()
        params = context['params']

        ingestion_output_path = params['ingestion_output_path']

        if not os.path.exists(ingestion_output_path):
            raise FileNotFoundError(
                f"Ingestion output not found at {ingestion_output_path}. "
                "Ensure nb_full_ingestion_KNMI.py has completed successfully."
            )

        with open(ingestion_output_path, 'r') as f:
            q_message = json.load(f)

        print(f"Read ingestion output: {q_message}")

        return q_message

    @task
    def create_queue_messages(q_message: dict):
        """Create queue messages for each downloaded file."""
        context = get_current_context()
        params = context['params']

        dataset = q_message.get('dataset')
        filepaths = q_message.get('filepath', [])
        run_id = q_message.get('run_id')
        source = q_message.get('source', params['source'])
        pipeline_name = q_message.get('pipeline_name', params['pipeline_name'])
        queue_name = params['queue_name']

        if not filepaths:
            print("No files to process")
            return []

        messages = []
        for filepath in filepaths:
            message = generate_queue_message(
                dataset=dataset,
                filepath=[filepath],  # One file per message
                source=source,
                pipeline_name=pipeline_name,
                queue_name=queue_name,
                run_id=run_id,
            )
            messages.append(message)
            print(f"Created message for {filepath}")

        print(f"Created {len(messages)} queue messages")

        return messages

    @task
    def send_to_queue(messages: list[dict]):
        """Send messages to Azure Queue Storage."""
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
        # for message in messages:
        #     queue_client.send_message(message['content'])

        if not messages:
            print("No messages to send")
            return []

        sent_message_ids = []
        for message in messages:
            content = json.loads(message['content'])
            print(f"Would send to queue: {content['queue_name']}")
            print(f"Dataset: {content['dataset']}")
            print(f"File: {content['filepath'][0]}")
            print(f"Message ID: {message['id']}")
            sent_message_ids.append(message['id'])

        print(f"Sent {len(sent_message_ids)} messages to queue")

        return sent_message_ids

    # Define task dependencies
    ingestion_output = read_ingestion_output()
    queue_messages = create_queue_messages(ingestion_output)
    send_to_queue(queue_messages)
