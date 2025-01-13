# IoT Sensor Dockerized Solution

This repository contains a Python-based solution for processing IoT sensor data, including database management, data preprocessing, metrics calculation, and visualization. The solution is containerized using Docker for easy deployment.

---

## Features
- Data Loading: Clean and load IoT sensor data into a SQLite database.
- Data Preprocessing: Normalize sensor values, handle missing timestamps, and prepare time-series data.
- Metrics Calculation: Calculate averages, maximums, and daily sums.
- Visualization: Generate plots to visualize sensor data.
- Reporting: Export metrics to CSV for further analysis.

---

## Requirements
- Docker 
- Python 3.10 (Optional for local testing)


## Steps to Execute

-- Without Docker (Local Environment)
Install dependencies:
" pip install -r requirements.txt "

Run the script:
" python iot_pipeline.py "

## Steps to Execute using Docker :
- Attached the Docker_documentation.txt for the reference.
