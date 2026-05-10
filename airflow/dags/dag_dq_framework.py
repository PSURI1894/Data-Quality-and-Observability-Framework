from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_sre',
    'start_date': datetime(2026, 5, 5),
    'retries': 0,
}

def calculate_slos():
    from framework.slo_tracker import SLOTracker
    tracker = SLOTracker("postgresql://postgres:postgres@postgres:5432/dq_observability")
    tracker.calculate_slo("db.payments.raw_events")

def detect_anomalies():
    from framework.anomaly_detector import AnomalyDetector
    detector = AnomalyDetector()
    print("Running windowed background anomaly calculations...")

with DAG(
    'dq_framework_background_jobs',
    default_args=default_args,
    schedule_interval='*/15 * * * *',
    catchup=False,
) as dag:

    run_slos = PythonOperator(
        task_id='calculate_slos',
        python_callable=calculate_slos,
    )

    run_anomalies = PythonOperator(
        task_id='background_anomaly_detection',
        python_callable=detect_anomalies,
    )

    run_slos >> run_anomalies
