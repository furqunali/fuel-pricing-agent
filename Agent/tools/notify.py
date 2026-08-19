# -*- coding: utf-8 -*-
"""TOOL: notify — team notification.

Phase 1: writes a plain notification file next to the reports (no email buttons).
Phase 2 (full automation): send a plain daily email via SMTP. The `send_email`
hook reads its configuration from environment variables (see `.env.example`) so
no credentials are ever hardcoded, and it can be switched on without touching the
rest of the agent.
"""
import os
import datetime

# Company/report label shown in the notification header. Override via env for
# your own deployment; defaults to a generic label in this public demo.
COMPANY_NAME = os.getenv("COMPANY_NAME", "Fuel Pricing")


def write_notice(output_dir, run_date, summary_lines):
    path = os.path.join(output_dir, "LAST RUN - notification.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("%s - Fuel Pricing update\n" % COMPANY_NAME)
        f.write("Run date: %s\n" % run_date)
        f.write("-" * 44 + "\n")
        for line in summary_lines:
            f.write(line + "\n")
        f.write("\nReports updated in this folder:\n")
        f.write("  - Fuel_Price_Tracker.xlsx\n")
        f.write("  - Demo_Fuel_Price_App.html\n")
    return path


def send_email(subject, body, to=None):
    """Stub for Phase 2. Wire an SMTP send here when full automation is on.

    Reads all connection details from environment variables so credentials are
    never stored in code (see `.env.example`):
        SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, NOTIFY_FROM, NOTIFY_TO
    """
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT", "587")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("NOTIFY_FROM", user)
    recipient = to or os.getenv("NOTIFY_TO")
    if not (host and user and password and recipient):
        raise NotImplementedError(
            "Email sending is enabled in Phase 2 (full automation). "
            "Set SMTP_HOST/SMTP_USER/SMTP_PASSWORD/NOTIFY_TO in your environment."
        )
    # Example wiring (kept minimal; enable in Phase 2):
    # import smtplib
    # from email.message import EmailMessage
    # msg = EmailMessage()
    # msg["Subject"], msg["From"], msg["To"] = subject, sender, recipient
    # msg.set_content(body)
    # with smtplib.SMTP(host, int(port)) as s:
    #     s.starttls()
    #     s.login(user, password)
    #     s.send_message(msg)
    raise NotImplementedError("Enable the SMTP block in send_email for Phase 2.")
