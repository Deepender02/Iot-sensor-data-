import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Database Configuration
DB_NAME = "iot_sensor_data.db"
TABLE_NAME = "sensor_data"

class DatabaseHandler:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None

    def connect(self):
        """Connect to the SQLite database."""
        self.connection = sqlite3.connect(self.db_name)

    def create_table(self, schema):
        """Create a table with the given schema."""
        with self.connection as conn:
            conn.execute(schema)

    def execute_query(self, query, params=None):
        """Execute a query with optional parameters."""
        with self.connection as conn:
            if params:
                conn.execute(query, params)
            else:
                conn.execute(query)

    def fetch_query(self, query, params=None):
        """Fetch results from a query."""
        with self.connection as conn:
            cursor = conn.execute(query, params or [])
            return cursor.fetchall()

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()

class DataLoader:
    def __init__(self, file_path, db_handler):
        self.file_path = file_path
        self.db_handler = db_handler

    def load_data(self):
        """Load data from CSV file."""
        data = pd.read_csv(self.file_path)
        return data

    def clean_data(self, data):
        """Clean and preprocess the data."""
        # Remove negative values in sensor readings
        data = data[data['sensor_value'] >= 0]
        # Drop rows with missing values
        data.dropna(inplace=True)
        return data

    def insert_data_to_db(self, data):
        """Insert cleaned data into the database."""
        data.to_sql(TABLE_NAME, self.db_handler.connection, if_exists='replace', index=False)

class DataPreProcessor:
    @staticmethod
    def normalize_data(data, column):
        """Normalize a column to be between 0 and 1."""
        data[column] = (data[column] - data[column].min()) / (data[column].max() - data[column].min())
        return data

    @staticmethod
    def fill_missing_timestamps(data, timestamp_column):
        """Fill missing timestamps using interpolation."""
        data[timestamp_column] = pd.to_datetime(data[timestamp_column])
        data = data.drop_duplicates(subset=timestamp_column)  # Remove duplicate timestamps
        data.set_index(timestamp_column, inplace=True)
        data = data.resample('1min').asfreq()  # Resample to 1-minute intervals
        data = data.infer_objects(copy=False)  # Ensure object dtype is correctly inferred
        for column in data.select_dtypes(include=['object']).columns:
            data[column] = pd.to_numeric(data[column], errors='coerce')  # Convert object columns to numeric where possible
        data = data.interpolate()  # Interpolate missing values
        data.reset_index(inplace=True)
        return data

class MetricsCalculator:
    @staticmethod
    def calculate_metrics(data):
        """Calculate averages, maximums, and daily sums."""
        data['date'] = pd.to_datetime(data['timestamp']).dt.date
        metrics = data.groupby('date').agg(
            avg_value=('sensor_value', 'mean'),
            max_value=('sensor_value', 'max'),
            daily_sum=('sensor_value', 'sum')
        ).reset_index()
        return metrics

    @staticmethod
    def total_power_per_site(db_handler):
        """Calculate total power consumption per site over two weeks."""
        query = """
        SELECT site_id, SUM(sensor_value) as total_power
        FROM sensor_data
        WHERE sensor_name = 'power_consumption'
        GROUP BY site_id
        """
        return db_handler.fetch_query(query)

    @staticmethod
    def highest_power_meter_per_site(db_handler):
        """Identify meters with the highest power consumption for each site."""
        query = """
        SELECT site_id, meter_id, MAX(total_power) as max_power
        FROM (
            SELECT site_id, meter_id, SUM(sensor_value) as total_power
            FROM sensor_data
            WHERE sensor_name = 'power_consumption'
            GROUP BY site_id, meter_id
        )
        GROUP BY site_id
        """
        return db_handler.fetch_query(query)

class GraphGenerator:
    @staticmethod
    def generate_graph(data, column, output_path):
        """Generate and save a graph as PNG."""
        plt.figure(figsize=(10, 6))
        data[column].plot(title=f"{column} Over Time")
        plt.xlabel("Time")
        plt.ylabel(column)
        plt.savefig(output_path)
        plt.close()

class DataReportGenerator:
    @staticmethod
    def export_to_csv(data, file_name):
        """Export data to a CSV file."""
        data.to_csv(file_name, index=False)

# Main Workflow
def main(file_path):
    # Initialize database handler
    db_handler = DatabaseHandler(DB_NAME)
    db_handler.connect()

    # Creating database schema
    schema = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        timestamp TEXT,
        site_id TEXT,
        meter_id TEXT,
        sensor_name TEXT,
        sensor_value REAL,
        status TEXT
    )
    """
    db_handler.create_table(schema)

    # Load and process data
    data_loader = DataLoader(file_path, db_handler)
    raw_data = data_loader.load_data()
    clean_data = data_loader.clean_data(raw_data)
    data_loader.insert_data_to_db(clean_data)

    # Perform data processing
    processor = DataPreProcessor()
    clean_data = processor.normalize_data(clean_data, 'sensor_value')
    clean_data = processor.fill_missing_timestamps(clean_data, 'timestamp')

    # Calculating metrics
    calculator = MetricsCalculator()
    metrics = calculator.calculate_metrics(clean_data)

    # Saving metrics to database
    metrics.to_sql('metrics', db_handler.connection, if_exists='replace', index=False)

    # Total power consumption per site
    total_power = calculator.total_power_per_site(db_handler)
    print("Total Power Consumption per Site:", total_power)

    # Highest power-consuming meter per site
    highest_power_meter = calculator.highest_power_meter_per_site(db_handler)
    print("Highest Power-Consuming Meter per Site:", highest_power_meter)

    # Generating graph
    graph_generator = GraphGenerator()
    graph_generator.generate_graph(clean_data, 'sensor_value', 'sensor_value_over_time.png')

    # Export metrics to CSV
    report_generator = DataReportGenerator()
    report_generator.export_to_csv(metrics, 'metrics_report.csv')

    db_handler.close()

# File path and execution
file_path = 'D:\\iot_sensor\\IoT_Sensor_Data.csv'
main(file_path)
