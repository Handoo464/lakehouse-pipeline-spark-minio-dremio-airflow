from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import pandas as pd
from minio import Minio
from minio.error import S3Error

# Define your default arguments
default_args = {
    'owner': 'coder2j',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

# Define your DAG
with DAG(
    dag_id='dag_minio_data_upload',
    default_args=default_args,
    description='Upload a dataset to MinIO',
    schedule_interval=None,  # Trigger manually for now
) as dag:

    def upload_to_minio(**kwargs):
        # Get environment variables for MinIO
        minio_endpoint = os.environ.get('MINIO_ENDPOINT', 'host.docker.internal:9000')  # MinIO server address
        access_key = os.environ.get('MINIO_ACCESS_KEY_ID', 'minioadmin')
        secret_key = os.environ.get('MINIO_SECRET_ACCESS_KEY', 'minioadmin')
        bucket_name = os.environ.get('MINIO_BUCKET_NAME', 'my-bucket')

        # Set up MinIO client
        minio_client = Minio(
            minio_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )

        # Create a dataset (this can be any simple dataset, for example, a CSV file)
        data = {
            'feature1': [1, 2, 3],
            'feature2': [4, 5, 6],
            'target': [7, 8, 9]
        }

        df = pd.DataFrame(data)
        file_path = "/opt/airflow/data/data.csv"
        df.to_csv(file_path, index=False)

        # Upload the dataset to MinIO
        dataset_key = "datasets/data.csv"
        try:
            minio_client.fput_object(bucket_name, dataset_key, file_path)
            print(f"Dataset uploaded to MinIO: s3://{bucket_name}/{dataset_key}")
        except S3Error as e:
            print(f"Error uploading dataset to MinIO: {e}")
            raise

    # Task to upload the dataset to MinIO
    upload_dataset_task = PythonOperator(
        task_id='upload_dataset_task',
        python_callable=upload_to_minio,
        provide_context=True,
        dag=dag,
    )
