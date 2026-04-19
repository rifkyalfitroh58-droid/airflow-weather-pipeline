from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.email import EmailOperator

from utils.extractor import extract_all_cities
from utils.transformer import transform_task
from utils.validator import check_quality_branch

def notify_failure(context):
    """Dipanggil otomatis oleh Airflow ketika task gagal."""
    task_id   = context["task_instance"].task_id
    dag_id    = context["task_instance"].dag_id
    exec_date = context["execution_date"]
    log_url   = context["task_instance"].log_url

    print(f"""
    ❌ PIPELINE GAGAL
    DAG     : {dag_id}
    Task    : {task_id}
    Tanggal : {exec_date}
    Log     : {log_url}
    """)

# ─── Default args untuk semua task ───────────────────────────────────────────
default_args = {
    "owner":            "data_engineer",
    "depends_on_past":  False,
    "retries":          2,                        # Retry 2x kalau gagal
    "retry_delay":      timedelta(minutes=5),     # Tunggu 5 menit sebelum retry
    "email_on_failure": False,
    "on_failure_callback": notify_failure,
}

# ─── Definisi DAG ─────────────────────────────────────────────────────────────
with DAG(
    dag_id="etl_weather_pipeline",
    description="ETL pipeline data cuaca dari Open-Meteo API ke PostgreSQL",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",         # Jalan otomatis setiap hari
    catchup=False,             # Jangan jalankan tanggal yang terlewat
    tags=["etl", "weather", "portofolio"],
) as dag:

    # Task 1: Extract
    extract = PythonOperator(
        task_id="extract_weather",
        python_callable=extract_all_cities,
    )

    # Task 2: Transform
    transform = PythonOperator(
        task_id="transform_weather",
        python_callable=transform_task,
    )

    # Task 3: Validasi — branching
    check_quality = BranchPythonOperator(
        task_id="check_data_quality",
        python_callable=check_quality_branch,
    )

    # Task 4a: Kalau valid
    quality_pass = EmptyOperator(task_id="quality_pass")

    # Task 4b: Kalau tidak valid — log error
    quality_fail = EmptyOperator(task_id="quality_fail")

    # Task 5: Load ke PostgreSQL
    load = PostgresOperator(
        task_id="load_to_postgres",
        postgres_conn_id="postgres_warehouse",
        sql="""
            INSERT INTO weather_raw
                (city, latitude, longitude, date,
                 temperature_max, temperature_min,
                 precipitation, windspeed_max)
            VALUES
            {% for rec in task_instance.xcom_pull(
                key='transformed_records',
                task_ids='transform_weather') %}
                (
                  '{{ rec.city }}', {{ rec.latitude }}, {{ rec.longitude }},
                  '{{ rec.date }}', {{ rec.temperature_max }},
                  {{ rec.temperature_min }}, {{ rec.precipitation }},
                  {{ rec.windspeed_max }}
                ){% if not loop.last %},{% endif %}
            {% endfor %}
            ON CONFLICT DO NOTHING;
        """,
        trigger_rule="none_failed_min_one_success",
    )

    # Task 6: Selesai
    done = EmptyOperator(task_id="pipeline_complete")

    # ─── Dependency / Urutan task ─────────────────────────────────────────────
    extract >> transform >> check_quality
    check_quality >> [quality_pass, quality_fail]
    quality_pass >> load >> done
    quality_fail >> done