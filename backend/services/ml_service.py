from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from backend.models import Expense, Prediction
from backend.extensions import db
from backend.services.analytics import CATEGORIES

DATASET_PATH = Path(__file__).resolve().parents[2] / "datasets" / "sample_expenses.csv"


def ensure_dataset():
    DATASET_PATH.parent.mkdir(exist_ok=True)
    if DATASET_PATH.exists():
        return DATASET_PATH
    rows = []
    rng = np.random.default_rng(42)
    for month in range(1, 25):
        for category in CATEGORIES:
            base = {
                "Bills": 720,
                "Food": 520,
                "Shopping": 310,
                "Travel": 230,
                "Entertainment": 180,
                "Health": 130,
                "Education": 110,
                "Investments": 260,
                "Others": 90,
            }[category]
            rows.append({
                "month_index": month,
                "category": category,
                "amount": round(max(20, base + rng.normal(0, 45) + month * rng.uniform(-2, 8)), 2),
            })
    pd.DataFrame(rows).to_csv(DATASET_PATH, index=False)
    return DATASET_PATH


def forecast_user(user_id):
    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.asc()).all()
    rows = []
    for item in expenses:
        rows.append({
            "month_index": item.date.year * 12 + item.date.month,
            "category_code": CATEGORIES.index(item.category) if item.category in CATEGORIES else len(CATEGORIES) - 1,
            "amount": item.amount,
            "category": item.category,
        })
    if len(rows) < 8:
        ensure_dataset()
        sample = pd.read_csv(DATASET_PATH)
        sample["category_code"] = sample["category"].apply(lambda c: CATEGORIES.index(c))
        rows = sample.to_dict("records")

    df = pd.DataFrame(rows)
    X = df[["month_index", "category_code"]]
    y = df["amount"]
    rf = RandomForestRegressor(n_estimators=80, random_state=7)
    lr = LinearRegression()
    rf.fit(X, y)
    lr.fit(X, y)
    next_month = int(df["month_index"].max()) + 1
    future = pd.DataFrame({"month_index": [next_month] * len(CATEGORIES), "category_code": list(range(len(CATEGORIES)))})
    rf_values = rf.predict(future)
    lr_values = lr.predict(future)
    blended = (rf_values * 0.7) + (lr_values * 0.3)
    total = round(float(blended.sum()), 2)
    top_idx = int(np.argmax(blended))
    previous = float(df[df["month_index"] == df["month_index"].max()]["amount"].sum())
    prediction = Prediction(
        user_id=user_id,
        predicted_expense=total,
        high_spending_category=CATEGORIES[top_idx],
        future_savings=round(max(0, previous - total), 2),
        model_name="Random Forest + Linear Regression",
    )
    db.session.add(prediction)
    db.session.commit()
    return {
        "prediction": prediction.to_dict(),
        "category_forecast": {CATEGORIES[i]: round(float(value), 2) for i, value in enumerate(blended)},
    }
