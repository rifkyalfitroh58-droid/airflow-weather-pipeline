import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CITIES = {
    "Jakarta":   {"latitude": -6.2088,  "longitude": 106.8456},
    "Surabaya":  {"latitude": -7.2575,  "longitude": 112.7521},
    "Bandung":   {"latitude": -6.9175,  "longitude": 107.6191},
    "Medan":     {"latitude":  3.5952,  "longitude":  98.6722},
}

def fetch_weather(city: str, lat: float, lon: float, days: int = 7) -> dict:
    """
    Ambil data cuaca dari Open-Meteo API.
    Gratis, tanpa API key.
    """
    end_date   = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":        lat,
        "longitude":       lon,
        "daily":           "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
        "timezone":        "Asia/Jakarta",
        "start_date":      str(start_date),
        "end_date":        str(end_date),
    }

    logger.info(f"Fetching weather data for {city}...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    logger.info(f"Berhasil fetch {len(data['daily']['time'])} hari untuk {city}")
    return {"city": city, "latitude": lat, "longitude": lon, "data": data}


def extract_all_cities(**context) -> list[dict]:
    """
    Extract data cuaca untuk semua kota.
    Return list of raw weather data — disimpan ke XCom.
    """
    results = []
    for city, coords in CITIES.items():
        try:
            result = fetch_weather(city, coords["latitude"], coords["longitude"])
            results.append(result)
        except Exception as e:
            logger.error(f"Gagal fetch {city}: {e}")

    logger.info(f"Total berhasil: {len(results)} dari {len(CITIES)} kota")

    # Push ke XCom agar bisa diakses task berikutnya
    context["ti"].xcom_push(key="raw_weather", value=results)
    return results