from pathlib import Path
from xml.parsers.expat import model
import joblib
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import train_test_split


DATA_PATH = Path("data/processed/taxi_tip_training_2024-01.parquet")
MODEL_PATH = Path("models/taxi_tip_lgbm_baseline.pkl")

TARGET_COLUMN = "tip_amount"
RANDOM_SEED = 42

def main() -> None:
    df = pd.read_parquet(DATA_PATH)

    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)

    model = LGBMRegressor(
            n_estimators=200,
            learning_rate=0.05,
            num_leaves=31,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = root_mean_squared_error(y_test, predictions)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"Train rows: {len(X_train):,}")
    print(f"Test rows: {len(X_test):,}")
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"Saved model to: {MODEL_PATH}")

if __name__ == "__main__":
    main()