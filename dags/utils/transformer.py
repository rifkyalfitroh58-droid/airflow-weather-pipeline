import pandas as pd
import logging

logger = logging.getLogger(__name__)


def transform_weather(raw_data: list[dict]) -> list[dict]:
    """
    Transformasi data mentah menjadi list of records
    yang siap dimasukkan ke tabel weather_raw.
    """
    records = []

    for item in raw_data:
        city      = item["city"]
        latitude  = item["latitude"]
        longitude = item["longitude"]
        daily     = item["data"]["daily"]

        for i, date in enumerate(daily["time"]):
            records.append({
                "city":            city,
                "latitude":        latitude,
                "longitude":       longitude,
                "date":            date,
                "temperature_max": daily["temperature_2m_max"][i],
                "temperature_min": daily["temperature_2m_min"][i],
                "precipitation":   daily["precipitation_sum"][i] or 0.0,
                "windspeed_max":   daily["windspeed_10m_max"][i],
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    logger.info(f"Transformasi selesai: {len(df)} baris dari {len(raw_data)} kota")
    return df.to_dict("records")


def transform_task(**context) -> None:
    """Wrapper untuk Airflow PythonOperator."""
    raw_data = context["ti"].xcom_pull(key="raw_weather", task_ids="extract_weather")

    if not raw_data:
        raise ValueError("Tidak ada data dari task extract_weather")

    records = transform_weather(raw_data)
    context["ti"].xcom_push(key="transformed_records", value=records)
    logger.info(f"Push {len(records)} records ke XCom")