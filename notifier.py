"""Send the report by SMTP email."""

from __future__ import annotations

import smtplib
from email.header import Header
from email.mime.text import MIMEText


def _clean_header_text(value) -> str:
    text = str(value or "").strip()
    for hidden in ("\u200b", "\ufeff", "\u200c", "\u200d"):
        text = text.replace(hidden, "")
    return text


def send_email(subject: str, body: str, email_config: dict) -> bool:
    required = ["sender", "password", "receiver", "smtp_host", "smtp_port"]
    missing = [key for key in required if not email_config.get(key)]
    if missing:
        print(f"이메일 설정이 부족해 발송하지 않았습니다: {', '.join(missing)}")
        return False

    sender = _clean_header_text(email_config["sender"])
    receiver = _clean_header_text(email_config["receiver"])
    password = _clean_header_text(email_config["password"])
    smtp_host = _clean_header_text(email_config["smtp_host"])

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = str(Header(_clean_header_text(subject), "utf-8"))
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP(smtp_host, int(email_config["smtp_port"])) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        return True
    except Exception as exc:
        print(f"이메일 발송 실패: {exc}")
        return False
