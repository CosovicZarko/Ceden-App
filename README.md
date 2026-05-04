# CEDEN Explorer

Interactive data exploration tool for the California Environmental Data Exchange Network (CEDEN) dataset.

---

## Overview

CEDEN Explorer is a local application designed to explore and analyze a large environmental dataset (~5GB) with a simple, intuitive interface.

It improves upon the standard CEDEN query experience by providing a more user-friendly workflow for selecting stations, exploring results, and working with the data.

---

## Features

* Interactive map for selecting monitoring stations
* Flexible filtering by species and sample identifiers
* Structured data exploration through a clean interface
* CSV export for further analysis
* Fast querying of large datasets using DuckDB

---

## Architecture

* **Backend:** FastAPI
* **Database Engine:** DuckDB (Parquet-based)
* **Frontend:** HTML + JavaScript
* **Data Pipeline:** Python (download, validation, transformation)

The application runs entirely locally and does not require any external services.

---

## Data Pipeline

* Downloads the latest dataset directly from CEDEN
* Validates dataset integrity before processing
* Transforms and organizes data for efficient querying
* Stores optimized Parquet file for fast access

---

## Technologies

Python · FastAPI · DuckDB · Pandas · JavaScript

---

## Notes

* Designed for straightforward use with minimal setup
* Handles large datasets efficiently on standard hardware
* Fully self-contained and portable
