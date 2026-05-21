from io import BytesIO, StringIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from backend.services.analytics import dashboard_summary, month_expenses


def csv_report(user_id):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Category", "Description", "Amount", "Payment Method", "Notes"])
    for item in month_expenses(user_id):
        writer.writerow([item.date.isoformat(), item.category, item.description, item.amount, item.payment_method, item.notes])
    return output.getvalue()


def pdf_report(user_id, user_name):
    summary = dashboard_summary(user_id)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("SmartSpend AI Monthly Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(72, 740, "SmartSpend AI Monthly Financial Report")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(72, 715, f"Prepared for: {user_name}")
    pdf.drawString(72, 690, f"Budget: ${summary['budget']['monthly_budget']:.2f}")
    pdf.drawString(72, 672, f"Expenses: ${summary['total_expenses']:.2f}")
    pdf.drawString(72, 654, f"Remaining: ${summary['remaining']:.2f}")
    pdf.drawString(72, 636, f"Health Score: {summary['financial_health_score']}/100")
    y = 600
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(72, y, "Category Breakdown")
    pdf.setFont("Helvetica", 10)
    for category, amount in summary["category_breakdown"].items():
        y -= 18
        pdf.drawString(88, y, f"{category}: ${amount:.2f}")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
