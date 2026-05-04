from fastapi import FastAPI, Query, HTTPException
import duckdb
import pandas as pd
from fastapi.responses import StreamingResponse, FileResponse
import io
import os

app = FastAPI()

DB_PATH = "data/ceden.parquet"


# --- SAFETY: ensure dataset exists ---
if not os.path.exists(DB_PATH):
    raise RuntimeError(
        "Dataset not found. Run: python pipeline/pipeline.py before starting the app."
    )


# --- QUERY HELPER ---
def query_db(sql: str) -> pd.DataFrame:
    try:
        df = duckdb.query(sql).df()
        df = df.fillna("")  # prevent JSON issues
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ROOT (SERVE FRONTEND) ---
@app.get("/")
def root():
    if not os.path.exists("index.html"):
        raise HTTPException(status_code=500, detail="index.html not found")
    return FileResponse("index.html")


# --- STATIONS ---
@app.get("/stations")
def get_stations():
    sql = f"""
        SELECT DISTINCT
            CompositeStationName AS name,
            TRY_CAST(CompositeLatitude AS DOUBLE) AS lat,
            TRY_CAST(CompositeLongitude AS DOUBLE) AS lon
        FROM '{DB_PATH}'
        WHERE TRY_CAST(CompositeLatitude AS DOUBLE) IS NOT NULL
          AND TRY_CAST(CompositeLongitude AS DOUBLE) IS NOT NULL
          AND TRY_CAST(CompositeLatitude AS DOUBLE) != -88
          AND TRY_CAST(CompositeLongitude AS DOUBLE) != -88
    """

    df = query_db(sql)
    return df.to_dict(orient="records")


# --- STATION DATA (MATCHES ORIGINAL BEHAVIOR) ---
@app.get("/station-data")
def get_station_data(
    names: str = Query(...),
    common_name: str = Query(None),
    composite_id: str = Query(None),
    per_station: int = 200
):
    station_list = [n.strip() for n in names.split(",") if n.strip()]

    if not station_list:
        return {"summary": [], "records": []}

    stations_sql = ", ".join(f"'{s}'" for s in station_list)

    sql = f"""
        SELECT *
        FROM '{DB_PATH}'
        WHERE CompositeStationName IN ({stations_sql})
    """

    df = query_db(sql)

    # --- FILTERS ---
    if common_name:
        df = df[df['CompositeCommonName'].str.upper().str.contains(common_name.upper(), na=False)]

    if composite_id:
        df = df[df['CompositeCompositeID'].str.upper().str.contains(composite_id.upper(), na=False)]

    # --- CLEAN RESULT COLUMN ---
    df['Result'] = pd.to_numeric(df['Result'], errors='coerce')
    df = df[df['Result'].notna()]

    # --- SUMMARY ---
    analytes = ['PCB', 'Mercury', 'Cadmium', 'DDT']
    summary_rows = []

    for ag in analytes:
        temp = df[df['Analyte_Group'].str.upper().str.strip() == ag.upper()]

        if not temp.empty:
            mean_val = round(temp['Result'].mean(), 2)
            min_val = round(temp['Result'].min(), 2)
            max_val = round(temp['Result'].max(), 2)
        else:
            mean_val = min_val = max_val = None

        summary_rows.append({
            "Analyte_Group": ag,
            "mean_result": mean_val if mean_val is not None else "N/A",
            "min_result": min_val if min_val is not None else "N/A",
            "max_result": max_val if max_val is not None else "N/A"
        })

    # --- RECORDS ---
    records = []
    for station in station_list:
        station_df = df[df["CompositeStationName"] == station].head(per_station)

        for _, row in station_df.iterrows():
            record = {
                col: val for col, val in row.items()
                if pd.notna(val) and val not in [float("inf"), float("-inf")]
            }
            records.append(record)

    return {"summary": summary_rows, "records": records}


# --- DOWNLOAD CSV ---
@app.get("/download-station-data")
def download_station_data(
    names: str = Query(...),
    common_name: str = Query(None),
    composite_id: str = Query(None)
):
    station_list = [n.strip() for n in names.split(",") if n.strip()]

    if not station_list:
        return StreamingResponse(io.StringIO(""), media_type="text/csv")

    stations_sql = ", ".join(f"'{s}'" for s in station_list)

    sql = f"""
        SELECT *
        FROM '{DB_PATH}'
        WHERE CompositeStationName IN ({stations_sql})
    """

    df = query_db(sql)

    if common_name:
        df = df[df['CompositeCommonName'].str.upper().str.contains(common_name.upper(), na=False)]

    if composite_id:
        df = df[df['CompositeCompositeID'].str.upper().str.contains(composite_id.upper(), na=False)]

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=stations.csv"}
    )