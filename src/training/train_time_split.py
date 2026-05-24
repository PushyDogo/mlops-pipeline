from pathlib import Path
import joblib
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, root_mean_squared_error
import json
import mlflow

DATA_PATH = Path("data/processed/taxi_tip_training_2024-01.parquet")
MODEL_PATH = Path("models/taxi_tip_lgbm_time_split.pkl")
METRICS_PATH = Path("models/taxi_tip_lgbm_time_split_metrics.json")
EXPERIMENT_NAME = "taxi-tip-prediction"

TARGET_COLUMN = "tip_amount"
TIME_COLUMN = "pickup_datetime"
RANDOM_SEED = 42


def main() -> None:
    df = pd.read_parquet(DATA_PATH)
    df = df.sort_values(TIME_COLUMN)

    split_index = int(len(df) * 0.8)

    train_df = df.iloc[:split_index]
    test_df = df.iloc[split_index:]

    X_train = train_df.drop(columns=[TARGET_COLUMN, TIME_COLUMN])
    y_train = train_df[TARGET_COLUMN]

    X_test = test_df.drop(columns=[TARGET_COLUMN, TIME_COLUMN])
    y_test = test_df[TARGET_COLUMN]

    params = {
        "n_estimators": 200,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "random_seed": RANDOM_SEED,
    }

    model = LGBMRegressor(
        n_estimators=params["n_estimators"],
        learning_rate=params["learning_rate"],
        num_leaves=params["num_leaves"],
        random_state=params["random_seed"],
        n_jobs=-1,
    )

    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run():
        mlflow.log_params(params)

        model.fit(X_train, y_train)

        predictions = model.predict(X_test)

        mae = mean_absolute_error(y_test, predictions)
        rmse = root_mean_squared_error(y_test, predictions)

        metrics = {
            "model_type": "LGBMRegressor",
            "split_type": "time",
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "train_start": str(train_df[TIME_COLUMN].min()),
            "train_end": str(train_df[TIME_COLUMN].max()),
            "test_start": str(test_df[TIME_COLUMN].min()),
            "test_end": str(test_df[TIME_COLUMN].max()),
            "mae": mae,
            "rmse": rmse,
            "random_seed": RANDOM_SEED,
        }

        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("train_rows", len(X_train))
        mlflow.log_metric("test_rows", len(X_test))

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, MODEL_PATH)

        with METRICS_PATH.open("w") as f:
            json.dump(metrics, f, indent=2)

        mlflow.log_artifact(str(MODEL_PATH))
        mlflow.log_artifact(str(METRICS_PATH))

        print(f"Train rows: {len(X_train):,}")
        print(f"Test rows: {len(X_test):,}")
        print(f"Train time range: {train_df[TIME_COLUMN].min()} to {train_df[TIME_COLUMN].max()}")
        print(f"Test time range: {test_df[TIME_COLUMN].min()} to {test_df[TIME_COLUMN].max()}")
        print(f"MAE: {mae:.4f}")
        print(f"RMSE: {rmse:.4f}")
        print(f"Saved model to: {MODEL_PATH}")
        print(f"Saved metrics to: {METRICS_PATH}")



if __name__ == "__main__":
    main()