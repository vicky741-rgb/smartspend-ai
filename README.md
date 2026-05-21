# SmartSpend AI - Financial Expense Tracking & Analytics System

SmartSpend AI is a full-stack personal finance app with secure accounts, budget tracking, expense management, analytics, ML forecasting, SMTP email alerts, exports, and an admin panel.

## Stack

- Frontend: HTML5, CSS3, JavaScript, Chart.js, Plotly, Streamlit companion dashboard
- Backend: Flask, SQLAlchemy, JWT
- Database: PostgreSQL via `DATABASE_URL`; local SQLite fallback for development
- Email: Gmail SMTP via environment variables
- ML: pandas, scikit-learn linear regression and random forest forecasting

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python backend\app.py
```

Open `http://127.0.0.1:5000`.

The first run creates demo data and an admin account:

- Email: `admin@smartspend.ai`
- Password: `Admin@12345`

## Production Configuration

Set these variables in `.env`:

```env
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me-too
DATABASE_URL=postgresql://user:password@localhost:5432/smartspend
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=SmartSpend AI <your-gmail@gmail.com>
```

For Gmail, use an app password instead of your normal account password.

## Features

- Registration, login, logout, forgot password, email verification tokens, JWT-secured APIs
- Per-user budgets, category budgets, expenses, reports, alerts, and predictions
- Live dashboard totals, spending status colors, Chart.js/Plotly analytics
- Overspending, savings, and exact-budget SMTP alert templates
- Expense CRUD with search and filters
- CSV and PDF report export
- Admin analytics and user management view
- ML prediction service using generated or imported finance datasets
- Streamlit analytics companion at `streamlit_app.py`
# SmartSpend AI

## Login Page
![Login](screenshots/login.png)

## Dashboard
![Dashboard](screenshots/dashboard.png)

## Analytics
![Analytics](screenshots/analytics.png)

## Prediction
![Prediction](screenshots/prediction.png)

## Add Expense
![Expense](screenshots/add_expense.png)


## Notes

SQLite fallback is included so the project runs immediately in a classroom/demo environment. Use PostgreSQL by setting `DATABASE_URL` for production-like deployment.
