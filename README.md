# 🌤️ Airflow Weather ETL Pipeline — Portofolio Data Engineering

> Automated ETL pipeline yang mengambil data cuaca dari **Open-Meteo API**, mentransformasikannya, memvalidasi kualitasnya, dan memuatnya ke **PostgreSQL** — diorkestrasikan secara terjadwal otomatis menggunakan **Apache Airflow** dan **Docker**.

---

## 📌 Deskripsi Project

Pipeline ini berjalan otomatis setiap hari tanpa intervensi manual. Data cuaca dari 4 kota besar Indonesia (Jakarta, Surabaya, Bandung, Medan) diambil dari Open-Meteo API, diproses melalui tahap transformasi dan validasi kualitas data, lalu dimuat ke PostgreSQL. Seluruh pipeline diorkestrasikan oleh Apache Airflow yang berjalan di dalam Docker container.

---

## 🏗️ Arsitektur Pipeline

```
Open-Meteo Weather API (Gratis, tanpa API key)
           │
           ▼
    extract_weather          ← PythonOperator: fetch data 4 kota
           │
           ▼
   transform_weather         ← PythonOperator: cleaning & normalisasi
           │
           ▼
   check_data_quality        ← BranchPythonOperator: validasi data
           │
     ┌─────┴─────┐
     ▼           ▼
quality_pass  quality_fail   ← Branch: valid vs invalid
     │
     ▼
load_to_postgres             ← PostgresOperator: upsert ke PostgreSQL
     │
     ▼
pipeline_complete            ← EmptyOperator: pipeline selesai
```

---

## 🛠️ Tech Stack

| Tools | Versi | Kegunaan |
|---|---|---|
| **Apache Airflow** | 2.8.0 | Orkestrasi & scheduling pipeline |
| **Docker** | Latest | Containerisasi Airflow & PostgreSQL |
| **PostgreSQL** | 15 | Database penyimpanan hasil ETL |
| **Python** | 3.11 | Bahasa utama pipeline |
| **Pandas** | 2.1.0 | Transformasi data |
| **Requests** | 2.31.0 | HTTP request ke Open-Meteo API |
| **pytest** | 7.4.0 | Unit testing komponen pipeline |

---

## 📂 Struktur Project

```
airflow-weather-pipeline/
│
├── dags/                            # Semua DAG Airflow
│   ├── weather_etl_dag.py           # DAG utama
│   └── utils/
│       ├── __init__.py
│       ├── extractor.py             # Logic extract dari API
│       ├── transformer.py           # Logic transformasi data
│       └── validator.py             # Logic validasi kualitas data
│
├── sql/
│   └── create_tables.sql            # DDL tabel PostgreSQL
│
├── tests/
│   ├── test_extractor.py
│   ├── test_transformer.py
│   └── test_validator.py
│
├── logs/                            # Airflow logs (auto-generated)
│   └── .gitkeep
│
├── plugins/                         # Airflow custom plugins
│   └── .gitkeep
│
├── docker-compose.yml               # Setup Airflow + PostgreSQL
├── .env.example                     # Template environment variable
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup & Cara Menjalankan

### Prerequisites
- Docker Desktop terinstall
- Minimal 10 GB free storage
- Minimal 8 GB RAM

### 1. Clone Repository

```bash
git clone https://github.com/username/airflow-weather-pipeline.git
cd airflow-weather-pipeline
```

### 2. Konfigurasi Environment Variable

```bash
cp .env.example .env
# Buka .env dan isi password PostgreSQL
```

Isi file `.env`:
```
POSTGRES_PASSWORD=password123
```

### 3. Jalankan Docker Compose

```bash
# Inisialisasi Airflow (hanya pertama kali)
docker-compose up airflow-init

# Jalankan semua service
docker-compose up -d

# Cek semua container berjalan
docker-compose ps
```

### 4. Buka Airflow UI

Buka browser: **http://localhost:8080**

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin` |

### 5. Jalankan Pipeline

1. Aktifkan DAG `etl_weather_pipeline` dengan toggle di UI
2. Klik tombol **Trigger DAG** untuk menjalankan manual pertama kali
3. Pantau progress di **Graph View** atau **Tree View**

### 6. Jalankan Unit Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan semua test
pytest tests/ -v
```

### 7. Matikan Docker (setelah selesai)

```bash
docker-compose down
```

---

## 🔁 Penjelasan DAG

### Konsep Utama

| Konsep | Implementasi |
|---|---|
| **DAG** | `etl_weather_pipeline` — pipeline didefinisikan sebagai kode Python |
| **Schedule** | `@daily` — pipeline jalan otomatis setiap hari |
| **Retry** | 2x retry dengan jeda 5 menit jika task gagal |
| **XCom** | Data antar task dibagikan via `xcom_push` dan `xcom_pull` |
| **Branching** | `BranchPythonOperator` memilih jalur valid atau invalid |
| **Catchup** | `False` — pipeline tidak menjalankan tanggal yang terlewat |

### Urutan Task

```
extract_weather
    └── transform_weather
            └── check_data_quality
                    ├── quality_pass ──► load_to_postgres ──► pipeline_complete
                    └── quality_fail ──────────────────────► pipeline_complete
```

---

## 📊 Sumber Data

**Open-Meteo API**
- URL: https://api.open-meteo.com
- Lisensi: Gratis untuk non-komersial
- Tidak membutuhkan API key
- Data tersedia: suhu, presipitasi, kecepatan angin

### Kota yang Dipantau

| Kota | Latitude | Longitude |
|---|---|---|
| Jakarta | -6.2088 | 106.8456 |
| Surabaya | -7.2575 | 112.7521 |
| Bandung | -6.9175 | 107.6191 |
| Medan | 3.5952 | 98.6722 |

---

## 🗄️ Schema Database

### Tabel `weather_raw`

| Kolom | Tipe | Deskripsi |
|---|---|---|
| `id` | SERIAL | Primary key auto-increment |
| `city` | VARCHAR | Nama kota |
| `latitude` | NUMERIC | Koordinat latitude |
| `longitude` | NUMERIC | Koordinat longitude |
| `date` | DATE | Tanggal data cuaca |
| `temperature_max` | NUMERIC | Suhu maksimum harian (°C) |
| `temperature_min` | NUMERIC | Suhu minimum harian (°C) |
| `precipitation` | NUMERIC | Total curah hujan (mm) |
| `windspeed_max` | NUMERIC | Kecepatan angin maksimum (km/h) |
| `extracted_at` | TIMESTAMP | Waktu data diambil |

### Tabel `weather_summary`

| Kolom | Tipe | Deskripsi |
|---|---|---|
| `id` | SERIAL | Primary key auto-increment |
| `city` | VARCHAR | Nama kota |
| `month` | VARCHAR | Bulan (format: YYYY-MM) |
| `avg_temp_max` | NUMERIC | Rata-rata suhu maksimum |
| `avg_temp_min` | NUMERIC | Rata-rata suhu minimum |
| `total_precipitation` | NUMERIC | Total curah hujan bulanan |
| `rainy_days` | INTEGER | Jumlah hari hujan |
| `updated_at` | TIMESTAMP | Waktu terakhir diupdate |

---

## ✅ Aturan Validasi Data

| Aturan | Detail |
|---|---|
| **Null check** | `city`, `date`, `temperature_max`, `temperature_min` tidak boleh null |
| **Range suhu** | Suhu harus antara -20°C hingga 60°C |
| **Logika suhu** | `temperature_max` harus lebih besar dari `temperature_min` |
| **Presipitasi** | Nilai curah hujan tidak boleh negatif |
| **Kecepatan angin** | Nilai windspeed tidak boleh melebihi 300 km/h |

---

## 🧠 Konsep Clean Code yang Diterapkan

| Prinsip | Implementasi |
|---|---|
| **Single Responsibility** | extractor, transformer, validator masing-masing punya satu tugas |
| **Separation of Concerns** | Utils dipisah dari DAG definition |
| **Modular Design** | Setiap komponen bisa ditest dan dijalankan secara independen |
| **Idempotency** | `ON CONFLICT DO NOTHING` mencegah duplikasi data |
| **Retry Mechanism** | Task otomatis diulang 2x jika gagal |
| **Branching Logic** | Pipeline mengambil jalur berbeda sesuai hasil validasi |
| **Environment Config** | Semua credentials dari `.env`, tidak di-hardcode |
| **Containerization** | Seluruh stack berjalan di Docker — reproducible di environment manapun |

---

## 🗺️ Portofolio Data Engineering

| Project | Teknologi | Konsep |
|---|---|---|
| [ETL Pipeline - Web Scraping](#) | Python, BeautifulSoup | Extract, Web Scraping |
| [dbt Transformation Pipeline](#) | Python, PostgreSQL, dbt | Transform, Data Modeling |
| [Batch ETL Pipeline](#) | Python, PostgreSQL, pytest | Load, Validation, Error Handling |
| **Airflow Weather Pipeline** | Airflow, Docker, PostgreSQL | Orchestration, Scheduling, Branching |

---

## 🚧 Status Project

> ⚠️ **Catatan:** Struktur kode dan konfigurasi sudah lengkap dan siap dijalankan. Pipeline belum dieksekusi karena keterbatasan storage untuk Docker. Akan dijalankan dan didokumentasikan hasilnya setelah environment siap.

---

## 👤 Author

**Nama Kamu**
- GitHub: [@rifkyalfitroh58-droid](https://github.com/username)
- LinkedIn: [linkedin.com/in/RifkyAlfitroh](https://linkedin.com/in/username)
