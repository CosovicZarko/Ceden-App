import os
import requests
import zipfile
import duckdb
import shutil

DATA_URL = os.getenv(
    "CEDEN_DATA_URL",
    "https://data.ca.gov/dataset/38cb5cca-1500-42e7-b359-e8e3c5d1e087/resource/dea5e450-4196-4a8a-afbb-e5eb89119516/download/tissuedata_parquet_2026-04-14.zip"
)

TEMP_DIR = "temp"
DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "ceden.parquet")


def clean_temp():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)


def download():
    zip_path = os.path.join(TEMP_DIR, "data.zip")

    print("Downloading dataset...")
    r = requests.get(DATA_URL, stream=True)
    r.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    return zip_path


def extract(zip_path):
    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(TEMP_DIR)


def validate(path):
    print("Validating...")

    count = duckdb.query(f"""
        SELECT COUNT(*) FROM '{path}/**/*.parquet'
    """).fetchone()[0]

    print(f"Row count: {count}")

    if count < 100000:
        raise Exception("Dataset too small — aborting")

    return True


def transform(input_path):
    print("Transforming...")

    output_temp = os.path.join(TEMP_DIR, "new.parquet")

    duckdb.execute(f"""
    COPY (
        SELECT *,
            CASE
                WHEN UPPER(Analyte) LIKE 'PCB%' THEN 'PCB'
                WHEN UPPER(Analyte) LIKE '%MERCURY%' THEN 'Mercury'
                WHEN UPPER(Analyte) LIKE '%CADMIUM%' THEN 'Cadmium'
                WHEN UPPER(Analyte) LIKE '%DDT%' 
                  OR UPPER(Analyte) LIKE '%DDE%' 
                  OR UPPER(Analyte) LIKE '%DDD%' THEN 'DDT'
                ELSE 'Other'
            END AS Analyte_Group
        FROM '{input_path}/**/*.parquet'
    )
    TO '{output_temp}' (FORMAT PARQUET)
    """)

    return output_temp


def replace_file(new_file):
    print("Replacing dataset...")

    os.makedirs(DATA_DIR, exist_ok=True)
    os.replace(new_file, OUTPUT_FILE)


def run():
    try:
        clean_temp()

        zip_path = download()
        extract(zip_path)

        parquet_path = TEMP_DIR

        validate(parquet_path)

        new_file = transform(parquet_path)

        replace_file(new_file)

        print("SUCCESS: dataset updated")

    except Exception as e:
        print("FAILED:", e)
        print("Old dataset preserved")


if __name__ == "__main__":
    run()