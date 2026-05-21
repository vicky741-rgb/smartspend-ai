from datetime import datetime
from flask import Blueprint, Response, jsonify, request, send_file, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from backend.email_service.mailer import finance_email, send_email
from backend.extensions import db
from backend.models import Budget, Expense, Notification, User
from backend.services.analytics import CATEGORIES, dashboard_summary, get_or_create_budget, month_expenses, previous_month_key
from backend.services.ml_service import forecast_user
from backend.services.reports import csv_report, pdf_report

api_bp = Blueprint("api", __name__, url_prefix="/api")


def active_user_id():
    try:
        identity = get_jwt_identity()
        if identity:
            return int(identity)
    except RuntimeError:
        pass
    return session.get("user_id")


def require_user():
    user_id = active_user_id()
    return User.query.get(user_id) if user_id else None


def maybe_send_budget_alert(user):
    summary = dashboard_summary(user.id)
    budget = summary["budget"]["monthly_budget"]
    total = summary["total_expenses"]
    previous = summary["previous_expenses"]
    if total > budget:
        subject = "Budget Alert - You Have Exceeded Your Monthly Budget"
        message = f"Expenses exceeded budget by ${total - budget:.2f}."
        theme = "red"
    elif total == budget and budget > 0:
        subject = "Budget Fully Utilized"
        message = "Budget fully used with no remaining savings."
        theme = "orange"
    elif total < previous:
        subject = "Congratulations! You Saved Money This Month"
        message = f"You saved ${previous - total:.2f} compared to last month."
        theme = "green"
    else:
        return
    recent = Notification.query.filter_by(user_id=user.id, type=theme, message=message).first()
    if recent:
        return
    db.session.add(Notification(user_id=user.id, type=theme, message=message))
    db.session.commit()
    html = finance_email(
        theme,
        subject,
        message,
        {
            "Budget": f"${budget:.2f}",
            "Expenses": f"${total:.2f}",
            "Previous Month": f"${previous:.2f}",
        },
    )
    send_email(user.email, subject, html)


@api_bp.get("/me")
def me():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(user.to_dict())


@api_bp.get("/dashboard")
def dashboard_api():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    forecast = forecast_user(user.id)
    summary = dashboard_summary(user.id)
    summary["prediction"] = forecast
    maybe_send_budget_alert(user)
    return jsonify(summary)


@api_bp.get("/expenses")
def list_expenses():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    query = Expense.query.filter_by(user_id=user.id)
    category = request.args.get("category")
    search = request.args.get("search")
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Expense.description.ilike(f"%{search}%"))
    return jsonify([item.to_dict() for item in query.order_by(Expense.date.desc()).all()])


@api_bp.post("/expenses")
def create_expense():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json() or {}
    expense = Expense(
        user_id=user.id,
        amount=float(data["amount"]),
        category=data.get("category", "Others"),
        description=data.get("description", ""),
        date=datetime.strptime(data.get("date"), "%Y-%m-%d").date() if data.get("date") else datetime.utcnow().date(),
        payment_method=data.get("payment_method", "Card"),
        notes=data.get("notes", ""),
    )
    db.session.add(expense)
    db.session.commit()
    maybe_send_budget_alert(user)
    return jsonify(expense.to_dict()), 201


@api_bp.put("/expenses/<int:expense_id>")
def update_expense(expense_id):
    user = require_user()
    expense = Expense.query.filter_by(id=expense_id, user_id=user.id if user else None).first_or_404()
    data = request.get_json() or {}
    for field in ["amount", "category", "description", "payment_method", "notes"]:
        if field in data:
            setattr(expense, field, float(data[field]) if field == "amount" else data[field])
    if data.get("date"):
        expense.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    db.session.commit()
    maybe_send_budget_alert(user)
    return jsonify(expense.to_dict())


@api_bp.delete("/expenses/<int:expense_id>")
def delete_expense(expense_id):
    user = require_user()
    expense = Expense.query.filter_by(id=expense_id, user_id=user.id if user else None).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted."})


@api_bp.get("/budget")
def get_budget():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_or_create_budget(user.id).to_dict())


@api_bp.post("/budget")
def set_budget():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json() or {}
    budget = get_or_create_budget(user.id, data.get("month"))
    budget.monthly_budget = float(data.get("monthly_budget", budget.monthly_budget))
    for category in CATEGORIES:
        key = f"{category.lower()}_budget"
        if key in data:
            setattr(budget, key, float(data[key]))
    db.session.commit()
    maybe_send_budget_alert(user)
    return jsonify(budget.to_dict())


@api_bp.get("/notifications")
def notifications():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify([item.to_dict() for item in Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()])


@api_bp.get("/analytics")
def analytics_api():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    monthly = db.session.query(
        func.strftime("%Y-%m", Expense.date).label("month"),
        func.sum(Expense.amount),
    ).filter_by(user_id=user.id).group_by("month").all()
    if db.engine.dialect.name != "sqlite":
        monthly = db.session.query(
            func.to_char(Expense.date, "YYYY-MM").label("month"),
            func.sum(Expense.amount),
        ).filter_by(user_id=user.id).group_by("month").all()
    forecast = forecast_user(user.id)
    return jsonify({
        "summary": dashboard_summary(user.id),
        "monthly": [{"month": month, "total": round(total or 0, 2)} for month, total in monthly],
        "forecast": forecast,
    })


@api_bp.get("/reports/csv")
def export_csv():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return Response(csv_report(user.id), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=smartspend-report.csv"})


@api_bp.get("/reports/pdf")
def export_pdf():
    user = require_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return send_file(pdf_report(user.id, user.name), mimetype="application/pdf", as_attachment=True, download_name="smartspend-report.pdf")


@api_bp.get("/admin/stats")
def admin_stats():
    user = require_user()
    if not user or user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({
        "total_users": User.query.count(),
        "total_expenses": round(db.session.query(func.sum(Expense.amount)).scalar() or 0, 2),
        "inactive_users": User.query.outerjoin(Expense).group_by(User.id).having(func.count(Expense.id) == 0).count(),
        "users": [item.to_dict() for item in User.query.order_by(User.created_at.desc()).all()],
    })
