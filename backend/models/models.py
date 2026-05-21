from datetime import datetime, date
import secrets
from backend.extensions import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(120), default=lambda: secrets.token_urlsafe(32))
    reset_token = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    budgets = db.relationship("Budget", backref="user", lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
        }


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    month = db.Column(db.String(7), nullable=False, index=True)
    monthly_budget = db.Column(db.Float, nullable=False, default=0)
    food_budget = db.Column(db.Float, default=0)
    shopping_budget = db.Column(db.Float, default=0)
    bills_budget = db.Column(db.Float, default=0)
    travel_budget = db.Column(db.Float, default=0)
    entertainment_budget = db.Column(db.Float, default=0)
    health_budget = db.Column(db.Float, default=0)
    education_budget = db.Column(db.Float, default=0)
    investments_budget = db.Column(db.Float, default=0)
    others_budget = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "month", name="unique_user_month_budget"),)

    def category_budgets(self):
        return {
            "Food": self.food_budget,
            "Shopping": self.shopping_budget,
            "Bills": self.bills_budget,
            "Travel": self.travel_budget,
            "Entertainment": self.entertainment_budget,
            "Health": self.health_budget,
            "Education": self.education_budget,
            "Investments": self.investments_budget,
            "Others": self.others_budget,
        }

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "month": self.month,
            "monthly_budget": self.monthly_budget,
            "category_budget": self.category_budgets(),
        }


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.String(255), default="")
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    payment_method = db.Column(db.String(50), default="Card")
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "date": self.date.isoformat(),
            "payment_method": self.payment_method,
            "notes": self.notes,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(40), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "message": self.message,
            "read": self.read,
            "created_at": self.created_at.isoformat(),
        }


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    predicted_expense = db.Column(db.Float, nullable=False)
    high_spending_category = db.Column(db.String(50), default="")
    future_savings = db.Column(db.Float, default=0)
    model_name = db.Column(db.String(80), default="Random Forest")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "predicted_expense": self.predicted_expense,
            "high_spending_category": self.high_spending_category,
            "future_savings": self.future_savings,
            "model_name": self.model_name,
            "created_at": self.created_at.isoformat(),
        }
