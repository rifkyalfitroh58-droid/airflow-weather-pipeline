CREATE TABLE IF NOT EXISTS weather_raw (
    id               SERIAL PRIMARY KEY,
    city             VARCHAR(100) NOT NULL,
    latitude         NUMERIC(8,4),
    longitude        NUMERIC(8,4),
    date             DATE NOT NULL,
    temperature_max  NUMERIC(5,2),
    temperature_min  NUMERIC(5,2),
    precipitation    NUMERIC(6,2),
    windspeed_max    NUMERIC(6,2),
    extracted_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather_summary (
    id               SERIAL PRIMARY KEY,
    city             VARCHAR(100) NOT NULL,
    month            VARCHAR(7) NOT NULL,
    avg_temp_max     NUMERIC(5,2),
    avg_temp_min     NUMERIC(5,2),
    total_precipitation NUMERIC(8,2),
    rainy_days       INTEGER,
    updated_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE (city, month)
);