from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 5),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'payment_ingestion_pipeline',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=False,
) as dag:

    ingest_events = BashOperator(
        task_id='ingest_raw_kafka_events',
        bash_command='python /framework/lineage.py --job ingest_raw_events',
    )

    dbt_build = BashOperator(
        task_id='dbt_run_and_test',
        bash_command='cd /dbt && dbt build',
    )

    run_validation = BashOperator(
        task_id='great_expectations_validation',
        bash_command='python /framework/validator.py --urn db.payments.raw_events',
    )

    ingest_events >> dbt_build >> run_validation
