from flask import Blueprint, redirect, render_template, session, url_for
from backend.models import User

pages_bp = Blueprint("pages", __name__)


def current_user():
    user_id = session.get("user_id")
    return User.query.get(user_id) if user_id else None


@pages_bp.get("/")
def welcome():
    if current_user():
        return redirect(url_for("pages.dashboard"))
    return render_template("welcome.html")


@pages_bp.get("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login_page"))
    return render_template("dashboard.html", user=user)


@pages_bp.get("/expenses")
def expenses():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login_page"))
    return render_template("expenses.html", user=user)


@pages_bp.get("/analytics")
def analytics():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login_page"))
    return render_template("analytics.html", user=user)


@pages_bp.get("/reports")
def reports():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login_page"))
    return render_template("reports.html", user=user)


@pages_bp.get("/settings")
@pages_bp.get("/profile")
@pages_bp.get("/notifications")
def settings():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login_page"))
    return render_template("settings.html", user=user)


@pages_bp.get("/admin")
def admin():
    user = current_user()
    if not user or user.role != "admin":
        return redirect(url_for("pages.dashboard"))
    return render_template("admin.html", user=user)


@pages_bp.get("/reset-password/<token>")
def reset_password_page(token):
    return render_template("reset_password.html", token=token)
