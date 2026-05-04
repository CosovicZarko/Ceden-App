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