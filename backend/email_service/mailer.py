import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app


def send_email(to_email, subject, html_body):
    username = current_app.config["MAIL_USERNAME"]
    password = current_app.config["MAIL_PASSWORD"]
    if not username or not password:
        current_app.logger.info("SMTP not configured; skipped email '%s' to %s", subject, to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(current_app.config["MAIL_SERVER"], current_app.config["MAIL_PORT"]) as server:
        if current_app.config["MAIL_USE_TLS"]:
            server.starttls()
        server.login(username, password)
        server.sendmail(msg["From"], [to_email], msg.as_string())
    return True


def finance_email(theme, title, body, stats):
    color = {"red": "#ff4d5e", "green": "#21c878", "orange": "#ffb84d", "blue": "#4d8dff"}[theme]
    cards = "".join(
        f"<td style='padding:14px;border-radius:14px;background:#101827;color:#fff'><b>{label}</b><br><span style='font-size:22px;color:{color}'>{value}</span></td>"
        for label, value in stats.items()
    )
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;background:#07111f;padding:30px;color:#dbe7ff">
      <div style="max-width:680px;margin:auto;border:1px solid rgba(255,255,255,.16);border-radius:24px;background:linear-gradient(135deg,rgba(255,255,255,.13),rgba(255,255,255,.04));padding:30px">
        <h1 style="color:{color};margin:0 0 10px">{title}</h1>
        <p style="font-size:16px;line-height:1.7">{body}</p>
        <table width="100%" cellspacing="10"><tr>{cards}</tr></table>
        <p style="color:#aab8d4">SmartSpend AI recommends reviewing category budgets, pausing nonessential purchases, and moving surplus into your savings goal.</p>
      </div>
    </div>
    """
