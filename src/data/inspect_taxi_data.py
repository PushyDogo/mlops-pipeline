from pathlib import Path
import pandas as pd


DATA_PATH = Path("data/raw/yellow_taxi/yellow_tripdata_2024-01.parquet")


def main():
    df = pd.read_parquet(DATA_PATH)

    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nDtypes:")
    print(df.dtypes)

    print("\nFirst rows:")
    print(df.head())

    print("\nMissing values:")
    print(df.isna().sum().sort_values(ascending=False).head(20))

    print("\nTarget summary: tip_amount")
    print(df["tip_amount"].describe())

if __name__ == "__main__":
    main()