"""Email delivery — same transport pattern as real-time-minaki-poc (SendGrid or SMTP)."""

import html
import logging
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import requests

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def _email_method() -> str:
    method = (os.getenv("EMAIL_METHOD") or "").lower()
    if method:
        return method
    return "sendgrid" if os.getenv("SENDGRID_API_KEY") else "smtp"


def smtp_configured() -> bool:
    if _email_method() == "sendgrid" and os.getenv("SENDGRID_API_KEY"):
        return True
    return bool(
        os.getenv("SMTP_HOST")
        and os.getenv("SMTP_USERNAME")
        and os.getenv("SMTP_PASSWORD")
    )


def _from_identity() -> tuple[str, str]:
    company = os.getenv("COMPANY_NAME", "CMA Assistant")
    smtp_user = os.getenv("SMTP_USERNAME", "")
    from_email = (
        os.getenv("SMTP_FROM_EMAIL")
        or os.getenv("FROM_EMAIL")
        or os.getenv("SMTP_FROM")
        or smtp_user
    )
    from_name = os.getenv("SMTP_FROM_NAME") or company
    return from_email, from_name


def send_email(
    *,
    to_email: str,
    subject: str,
    plain: str,
    html_body: str | None = None,
) -> dict[str, Any]:
    """Send plain (+ optional HTML) email via SendGrid or SMTP (minaki-compatible)."""
    to_addr = to_email.strip()
    if not is_valid_email(to_addr):
        return {"success": False, "error": f"Invalid email: {to_addr}"}

    if not smtp_configured():
        logger.info("Email not configured — skipping send to %s", to_addr)
        return {"success": False, "error": "Email not configured (SendGrid or SMTP)"}

    from_email, from_name = _from_identity()
    method = _email_method()

    if method == "sendgrid" and os.getenv("SENDGRID_API_KEY"):
        content: list[dict[str, str]] = [{"type": "text/plain", "value": plain}]
        if html_body:
            content.append({"type": "text/html", "value": html_body})
        email_data = {
            "personalizations": [{"to": [{"email": to_addr}], "subject": subject}],
            "from": {"email": from_email, "name": from_name},
            "content": content,
        }
        try:
            r = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {os.getenv('SENDGRID_API_KEY')}",
                    "Content-Type": "application/json",
                },
                json=email_data,
                timeout=30,
            )
            if r.status_code == 202:
                logger.info("Email sent via SendGrid to %s", to_addr)
                return {"success": True, "message": f"Email sent to {to_addr}"}
            return {"success": False, "error": f"SendGrid {r.status_code}: {r.text}"}
        except Exception as e:
            logger.error("SendGrid failed for %s: %s", to_addr, e)
            return {"success": False, "error": str(e)}

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    if not all([smtp_host, smtp_username, smtp_password]):
        return {"success": False, "error": "SMTP not configured"}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_addr
    msg.attach(MIMEText(plain, "plain"))
    if html_body:
        msg.attach(MIMEText(html_body, "html"))

    try:
        if use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, [to_addr], msg.as_string())
        server.quit()
        logger.info("Email sent via SMTP to %s", to_addr)
        return {"success": True, "message": f"Email sent to {to_addr}"}
    except smtplib.SMTPAuthenticationError as e:
        error = str(e)
        if "gmail.com" in (smtp_host or "").lower() or "gsmtp" in error.lower():
            error = (
                "Gmail SMTP auth failed — use an App Password, not your regular password. "
                "See https://myaccount.google.com/apppasswords"
            )
        logger.error("SMTP auth failed for %s: %s", to_addr, error)
        return {"success": False, "error": error}
    except Exception as e:
        logger.error("SMTP failed for %s: %s", to_addr, e)
        return {"success": False, "error": str(e)}


def send_cma_report(
    *,
    to_email: str,
    subject_property: str,
    report_markdown: str,
    recommended_price: str | None = None,
) -> bool:
    """Email CMA report to user. Returns True if sent."""
    subject = f"Your CMA Report — {subject_property[:60]}"
    if recommended_price:
        subject += f" (Est. {recommended_price})"

    price_line = f"Recommended price: {recommended_price}\n" if recommended_price else ""
    plain = f"""Hi,

Your Comparative Market Analysis is ready.

Property: {subject_property}
{price_line}
---
{report_markdown}
---

This report was generated by the CMA Assistant.
""".strip()

    safe_report = html.escape(report_markdown, quote=True)
    html_body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family: system-ui, sans-serif; line-height: 1.5; color: #222;">
<p>Your Comparative Market Analysis is ready.</p>
<p><strong>Property:</strong> {html.escape(subject_property, quote=True)}<br>
{f"<strong>Recommended price:</strong> {html.escape(recommended_price, quote=True)}<br>" if recommended_price else ""}
</p>
<pre style="white-space: pre-wrap; background: #f6f8fa; padding: 12px; border-radius: 8px; font-size: 13px;">{safe_report}</pre>
<p style="color:#666;font-size:12px;">Generated by the CMA Assistant.</p>
</body></html>"""

    result = send_email(
        to_email=to_email,
        subject=subject,
        plain=plain,
        html_body=html_body,
    )
    return bool(result.get("success"))
