from pathlib import Path
import pandas as pd


RAW_DATA_PATH = Path("data/raw/yellow_taxi/yellow_tripdata_2024-01.parquet")
OUTPUT_PATH = Path("data/processed/taxi_tip_training_2024-01.parquet")

MIN_PICKUP_DATETIME = "2024-01-01"
MAX_PICKUP_DATETIME = "2024-02-01"

FEATURE_COLUMNS = [
    "VendorID",
    "passenger_count",
    "trip_distance",
    "RatecodeID",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "extra",
    "mta_tax",
    "tolls_amount",
    "improvement_surcharge",
    "congestion_surcharge",
    "Airport_fee",
    "pickup_hour",
    "pickup_day_of_week",
    "trip_duration_minutes",
    "pickup_datetime",
]

TARGET_COLUMN = "tip_amount"

def main():
    df = pd.read_parquet(RAW_DATA_PATH)

    df["trip_duration_minutes"] = (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]).dt.total_seconds() / 60
    df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour
    df["pickup_day_of_week"] = df["tpep_pickup_datetime"].dt.dayofweek
    df["pickup_datetime"] = df["tpep_pickup_datetime"]

    df = df[FEATURE_COLUMNS + [TARGET_COLUMN]]

    df = df[
        (df["pickup_datetime"] >= MIN_PICKUP_DATETIME)
        & (df["pickup_datetime"] < MAX_PICKUP_DATETIME)
        & (df["tip_amount"] >= 0)
        & (df["tip_amount"] <= 100)
        & (df["fare_amount"] > 0)
        & (df["trip_distance"] > 0)
        & (df["trip_duration_minutes"] > 0)
        & (df["trip_duration_minutes"] <= 180)
    ]

    df = df.dropna()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)

    print(f"Wrote {OUTPUT_PATH}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {df.columns.tolist()}")
    print("\nTarget summary:")
    print(df[TARGET_COLUMN].describe())

if __name__ == "__main__":
    main()