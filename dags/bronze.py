from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import requests
from minio import Minio
from minio.error import S3Error

# Define default arguments
default_args = {
    'owner': 'airflow_user',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

# Define MinIO parameters
minio_endpoint = 'host.docker.internal:9000'  # MinIO server address
access_key = 'minioadmin'
secret_key = 'minioadmin'
bucket_name = 'my-bucket'

# List of CSV files with their public URLs
csv_urls = [
    'https://raw.githubusercontent.com/DataWithBaraa/sql-data-warehouse-project/main/datasets/source_crm/cust_info.csv',
    'https://raw.githubusercontent.com/DataWithBaraa/sql-data-warehouse-project/main/datasets/source_crm/prd_info.csv',
    'https://raw.githubusercontent.com/DataWithBaraa/sql-data-warehouse-project/main/datasets/source_crm/sales_details.csv',
    'https://github.com/DataWithBaraa/sql-data-warehouse-project/blob/main/datasets/source_erp/CUST_AZ12.csv',
    'https://github.com/DataWithBaraa/sql-data-warehouse-project/blob/main/datasets/source_erp/LOC_A101.csv',
    'https://github.com/DataWithBaraa/sql-data-warehouse-project/blob/main/datasets/source_erp/PX_CAT_G1V2.csv',
]

# Set up MinIO client
minio_client = Minio(
    minio_endpoint,
    access_key=access_key,
    secret_key=secret_key,
    secure=False
)

# Create bucket if it doesn't exist
if not minio_client.bucket_exists(bucket_name):
    minio_client.make_bucket(bucket_name)

# Define the function to download file and upload to MinIO
def download_and_upload_to_minio(url, file_name, bucket_name):
    try:
        # Download file from URL
        response = requests.get(url)
        if response.status_code == 200:
            # Save to a temporary file
            temp_file_path = f'/tmp/{file_name}'
            with open(temp_file_path, 'wb') as f:
                f.write(response.content)

            # Upload to MinIO
            minio_client.fput_object(bucket_name, file_name, temp_file_path)
            print(f"File {file_name} uploaded to MinIO: s3://{bucket_name}/{file_name}")

            # Optionally, remove the temporary file
            os.remove(temp_file_path)
        else:
            print(f"Failed to download {file_name} from URL. HTTP Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {file_name}: {e}")
    except S3Error as e:
        print(f"Error uploading {file_name} to MinIO: {e}")

# Define the DAG
with DAG(
    dag_id='minio_csv_upload_dag',
    default_args=default_args,
    description='Download CSV files from URLs and upload to MinIO',
    schedule_interval=None,  # Trigger manually
    catchup=False
) as dag:

    # Task to upload each CSV file to MinIO
    for url in csv_urls:
        file_name = url.split('/')[-1]  # Extract file name from URL

        # Define PythonOperator for each file upload task
        upload_task = PythonOperator(
            task_id=f'upload_{file_name.replace(".", "_")}',
            python_callable=download_and_upload_to_minio,
            op_args=[url, file_name, bucket_name],
            dag=dag,
        )
