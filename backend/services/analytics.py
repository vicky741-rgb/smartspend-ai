from collections import defaultdict
from datetime import date, timedelta
from sqlalchemy import extract
from backend.extensions import db
from backend.models import Budget, Expense

CATEGORIES = ["Food", "Shopping", "Bills", "Travel", "Entertainment", "Health", "Education", "Investments", "Others"]


def month_key(value=None):
    value = value or date.today()
    return value.strftime("%Y-%m")


def previous_month_key(value=None):
    value = value or date.today()
    first = value.replace(day=1)
    prev = first - timedelta(days=1)
    return prev.strftime("%Y-%m")


def month_expenses(user_id, month=None):
    month = month or month_key()
    year, mon = map(int, month.split("-"))
    return Expense.query.filter(
        Expense.user_id == user_id,
        extract("year", Expense.date) == year,
        extract("month", Expense.date) == mon,
    ).all()


def get_or_create_budget(user_id, month=None):
    month = month or month_key()
    budget = Budget.query.filter_by(user_id=user_id, month=month).first()
    if not budget:
        budget = Budget(user_id=user_id, month=month, monthly_budget=2500)
        budget.food_budget = 550
        budget.shopping_budget = 350
        budget.bills_budget = 700
        budget.travel_budget = 250
        budget.entertainment_budget = 220
        budget.health_budget = 150
        budget.education_budget = 120
        budget.investments_budget = 100
        budget.others_budget = 60
        db.session.add(budget)
        db.session.commit()
    return budget


def dashboard_summary(user_id):
    budget = get_or_create_budget(user_id)
    expenses = month_expenses(user_id)
    prev_expenses = month_expenses(user_id, previous_month_key())
    total = round(sum(item.amount for item in expenses), 2)
    prev_total = round(sum(item.amount for item in prev_expenses), 2)
    remaining = round(budget.monthly_budget - total, 2)
    utilization = round((total / budget.monthly_budget * 100), 1) if budget.monthly_budget else 0
    status = "green"
    if total > budget.monthly_budget:
        status = "red"
    elif total == budget.monthly_budget or utilization >= 85:
        status = "orange"

    by_category = defaultdict(float)
    by_day = defaultdict(float)
    for item in expenses:
        by_category[item.category] += item.amount
        by_day[item.date.isoformat()] += item.amount

    savings_delta = round(prev_total - total, 2)
    financial_health = max(0, min(100, round(100 - utilization * 0.6 + (10 if savings_delta > 0 else -8))))

    recommendations = []
    if total > budget.monthly_budget:
        recommendations.append("Pause discretionary spending until the next cycle and review your top two categories.")
    if savings_delta > 0:
        recommendations.append(f"You spent ${savings_delta:.2f} less than last month. Move part of it into savings.")
    top_category = max(by_category, key=by_category.get) if by_category else "Food"
    recommendations.append(f"Your highest category is {top_category}. Set a weekly cap to smooth the trend.")

    return {
        "budget": budget.to_dict(),
        "total_expenses": total,
        "previous_expenses": prev_total,
        "remaining": remaining,
        "savings": max(0, remaining),
        "utilization": utilization,
        "status": status,
        "category_breakdown": dict(by_category),
        "daily_spending": dict(sorted(by_day.items())),
        "financial_health_score": financial_health,
        "recommendations": recommendations,
    }
