from datetime import date, timedelta
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from backend.auth.routes import auth_bp
from backend.config import Config
from backend.extensions import bcrypt, db, jwt
from backend.models import Budget, Expense, User
from backend.routes.api import api_bp
from backend.routes.pages import pages_bp
from backend.services.analytics import CATEGORIES
from backend.services.ml_service import ensure_dataset


def create_app():
    app = Flask(
        __name__,
        template_folder=str(ROOT / "frontend" / "templates"),
        static_folder=str(ROOT / "frontend" / "static"),
    )
    app.config.from_object(Config)
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app, supports_credentials=True)
    csrf = CSRFProtect(app)
    csrf.exempt(api_bp)
    csrf.exempt(auth_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)
    with app.app_context():
        db.create_all()
        ensure_dataset()
        seed_demo_data()
    return app


def seed_demo_data():
    if User.query.filter_by(email="admin@smartspend.ai").first():
        return
    admin = User(name="SmartSpend Admin", email="admin@smartspend.ai", role="admin", is_verified=True)
    admin.set_password("Admin@12345")
    user = User(name="Demo Investor", email="demo@smartspend.ai", role="user", is_verified=True)
    user.set_password("Demo@12345")
    db.session.add_all([admin, user])
    db.session.flush()
    today = date.today()
    for owner in [admin, user]:
        for offset in [1, 0]:
            month_date = (today.replace(day=1) - timedelta(days=offset * 28)).replace(day=1)
            month = month_date.strftime("%Y-%m")
            budget = Budget(user_id=owner.id, month=month, monthly_budget=3200 if owner.role == "admin" else 2600)
            budget.food_budget = 650
            budget.shopping_budget = 400
            budget.bills_budget = 850
            budget.travel_budget = 300
            budget.entertainment_budget = 240
            budget.health_budget = 180
            budget.education_budget = 120
            budget.investments_budget = 300
            budget.others_budget = 160
            db.session.add(budget)
            for day in range(1, 24, 3):
                category = random.choice(CATEGORIES)
                amount = round(random.uniform(18, 220), 2)
                if category == "Bills":
                    amount += 260
                db.session.add(
                    Expense(
                        user_id=owner.id,
                        amount=amount,
                        category=category,
                        description=f"{category} expense",
                        date=month_date.replace(day=min(day, 25)),
                        payment_method=random.choice(["Card", "UPI", "Cash", "Bank Transfer"]),
                        notes="Seeded demo transaction",
                    )
                )
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
