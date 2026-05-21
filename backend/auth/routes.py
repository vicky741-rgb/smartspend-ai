import secrets
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for, current_app
from flask_jwt_extended import create_access_token
from backend.email_service.mailer import send_email
from backend.extensions import db
from backend.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/api/register")
def register():
    data = request.get_json() or {}
    if not data.get("email") or not data.get("password") or not data.get("name"):
        return jsonify({"error": "Name, email, and password are required."}), 400
    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Email already registered."}), 409
    user = User(name=data["name"].strip(), email=data["email"].lower().strip())
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    verify_url = f"{current_app.config['APP_BASE_URL']}/verify-email/{user.verification_token}"
    send_email(
        user.email,
        "Verify your SmartSpend AI account",
        f"<h2>Welcome to SmartSpend AI</h2><p>Verify your email:</p><p><a href='{verify_url}'>Verify account</a></p>",
    )
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    session["user_id"] = user.id
    return jsonify({"token": token, "user": user.to_dict(), "message": "Registered successfully. Verification email sent if SMTP is configured."})


@auth_bp.post("/api/login")
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=(data.get("email") or "").lower().strip()).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"error": "Invalid email or password."}), 401
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    session["user_id"] = user.id
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.post("/api/forgot-password")
def forgot_password():
    data = request.get_json() or {}
    user = User.query.filter_by(email=(data.get("email") or "").lower().strip()).first()
    if user:
        user.reset_token = secrets.token_urlsafe(32)
        db.session.commit()
        reset_url = f"{current_app.config['APP_BASE_URL']}/reset-password/{user.reset_token}"
        send_email(user.email, "Reset your SmartSpend AI password", f"<p>Reset your password here: <a href='{reset_url}'>Reset password</a></p>")
    return jsonify({"message": "If the email exists, a reset link has been sent."})


@auth_bp.post("/api/reset-password/<token>")
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first_or_404()
    data = request.get_json() or {}
    if len(data.get("password", "")) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    user.set_password(data["password"])
    user.reset_token = None
    db.session.commit()
    return jsonify({"message": "Password updated."})


@auth_bp.get("/verify-email/<token>")
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first_or_404()
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    return redirect(url_for("pages.dashboard"))


@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("pages.login"))


@auth_bp.get("/login")
def login_page():
    return render_template("login.html")
