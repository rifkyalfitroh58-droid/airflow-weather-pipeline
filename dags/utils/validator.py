import logging

logger = logging.getLogger(__name__)

MAX_TEMP  = 60.0   # Suhu max realistis (Celsius)
MIN_TEMP  = -20.0  # Suhu min realistis
MAX_WIND  = 300.0  # Kecepatan angin max realistis (km/h)


def validate_records(records: list[dict]) -> tuple[bool, list[str]]:
    """
    Validasi kualitas data hasil transformasi.
    Return (is_valid, list_of_errors).
    """
    errors = []

    if not records:
        errors.append("Tidak ada records untuk divalidasi")
        return False, errors

    for i, rec in enumerate(records):
        # Cek null
        for field in ["city", "date", "temperature_max", "temperature_min"]:
            if rec.get(field) is None:
                errors.append(f"Record {i}: field '{field}' null")

        # Cek range suhu
        if rec.get("temperature_max") and not (MIN_TEMP <= rec["temperature_max"] <= MAX_TEMP):
            errors.append(f"Record {i} ({rec['city']}): temperature_max {rec['temperature_max']} di luar range")

        # Cek logika: max harus >= min
        if rec.get("temperature_max") and rec.get("temperature_min"):
            if rec["temperature_max"] < rec["temperature_min"]:
                errors.append(f"Record {i} ({rec['city']}): temp_max < temp_min")

        # Cek precipitasi tidak negatif
        if rec.get("precipitation") and rec["precipitation"] < 0:
            errors.append(f"Record {i} ({rec['city']}): precipitation negatif")

    is_valid = len(errors) == 0
    if is_valid:
        logger.info(f"Validasi PASS: {len(records)} records OK")
    else:
        logger.warning(f"Validasi FAIL: {len(errors)} error ditemukan")

    return is_valid, errors


def check_quality_branch(**context) -> str:
    """
    BranchPythonOperator — return nama task yang akan dijalankan.
    """
    records = context["ti"].xcom_pull(
        key="transformed_records", task_ids="transform_weather"
    )
    is_valid, errors = validate_records(records or [])

    context["ti"].xcom_push(key="validation_errors", value=errors)

    # Return nama task sesuai hasil validasi
    return "quality_pass" if is_valid else "quality_fail"