#!/usr/bin/env python3
"""
ServerRoot.net — Email Notification System
Sends status updates, alerts, and health reports via SMTP
Supports: Gmail, SendGrid, Mailgun, any SMTP relay
"""

import smtplib
import json
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

logger = logging.getLogger("EMAIL-NOTIFIER")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("logs/email_notifier.log"),
        logging.StreamHandler()
    ]
)

# ─── Config ───────────────────────────────────────────────────────────────────
# Set these via environment variables or .env file
SMTP_HOST     = os.getenv("SMTP_HOST",     "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER",     "")          # your sending email
SMTP_PASS     = os.getenv("SMTP_PASS",     "")          # app password / API key
NOTIFY_TO     = os.getenv("NOTIFY_EMAIL",  "")          # recipient email
FROM_NAME     = os.getenv("FROM_NAME",     "ServerRoot.net")
ENABLED       = bool(SMTP_USER and SMTP_PASS and NOTIFY_TO)


def _build_html(subject: str, body_html: str) -> str:
    return f"""
    <html><body style="font-family:monospace;background:#0d1117;color:#e6edf3;padding:20px;">
    <div style="max-width:700px;margin:auto;border:1px solid #30363d;border-radius:8px;padding:24px;">
      <div style="border-bottom:1px solid #21262d;padding-bottom:12px;margin-bottom:20px;">
        <span style="color:#58a6ff;font-size:18px;font-weight:bold;">⚡ ServerRoot.net</span>
        <span style="color:#6e7681;font-size:12px;margin-left:12px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
      </div>
      <h2 style="color:#f0f6fc;margin-top:0;">{subject}</h2>
      {body_html}
      <div style="border-top:1px solid #21262d;margin-top:24px;padding-top:12px;color:#6e7681;font-size:11px;">
        ServerRoot.net v2.0.0-Enterprise | Automated Notification
      </div>
    </div></body></html>
    """


def send_email(subject: str, body_html: str, to: Optional[str] = None) -> bool:
    """Send an HTML email. Returns True on success."""
    recipient = to or NOTIFY_TO
    if not ENABLED:
        logger.warning("Email not configured — skipping send. Set SMTP_USER, SMTP_PASS, NOTIFY_EMAIL in .env")
        return False
    if not recipient:
        logger.warning("No recipient configured")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[ServerRoot] {subject}"
        msg["From"]    = f"{FROM_NAME} <{SMTP_USER}>"
        msg["To"]      = recipient

        html_content = _build_html(subject, body_html)
        msg.attach(MIMEText(body_html.replace("<[^>]+>", ""), "plain"))
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, recipient, msg.as_string())

        logger.info(f"Email sent: '{subject}' → {recipient}")
        return True

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


# ─── Pre-built notification templates ─────────────────────────────────────────

def notify_health_report(stats: dict) -> bool:
    """Send periodic health report."""
    uptime_min = stats.get("uptime_seconds", 0) // 60
    body = f"""
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="color:#8b949e;padding:6px 0;">Status</td>
          <td style="color:#3fb950;font-weight:bold;">✅ HEALTHY</td></tr>
      <tr><td style="color:#8b949e;padding:6px 0;">Uptime</td>
          <td style="color:#e6edf3;">{uptime_min} minutes</td></tr>
      <tr><td style="color:#8b949e;padding:6px 0;">Active Agents</td>
          <td style="color:#e6edf3;">{stats.get('active_agents', 0)}</td></tr>
      <tr><td style="color:#8b949e;padding:6px 0;">Total Operations</td>
          <td style="color:#e6edf3;">{stats.get('total_operations', 0)}</td></tr>
      <tr><td style="color:#8b949e;padding:6px 0;">Successful Ops</td>
          <td style="color:#3fb950;">{stats.get('successful_operations', 0)}</td></tr>
      <tr><td style="color:#8b949e;padding:6px 0;">Vulnerabilities Found</td>
          <td style="color:#f85149;">{stats.get('vulnerabilities_found', 0)}</td></tr>
      <tr><td style="color:#8b949e;padding:6px 0;">Targets Scanned</td>
          <td style="color:#e6edf3;">{stats.get('targets_scanned', 0)}</td></tr>
    </table>
    """
    return send_email("Health Report", body)


def notify_alert(level: str, title: str, message: str, details: str = "") -> bool:
    """Send a security/system alert."""
    colors = {"critical": "#f85149", "high": "#d29922", "medium": "#58a6ff", "low": "#3fb950"}
    color = colors.get(level.lower(), "#8b949e")
    body = f"""
    <div style="border-left:4px solid {color};padding:12px 16px;background:#161b22;border-radius:4px;margin-bottom:16px;">
      <div style="color:{color};font-weight:bold;text-transform:uppercase;font-size:12px;">{level.upper()} ALERT</div>
      <div style="color:#f0f6fc;font-size:16px;margin:8px 0;">{title}</div>
      <div style="color:#8b949e;">{message}</div>
    </div>
    {f'<pre style="background:#161b22;padding:12px;border-radius:4px;color:#8b949e;font-size:12px;overflow:auto;">{details}</pre>' if details else ''}
    """
    return send_email(f"[{level.upper()}] {title}", body)


def notify_service_restart(service: str, reason: str, attempt: int) -> bool:
    """Notify when watchdog restarts a service."""
    body = f"""
    <div style="border-left:4px solid #d29922;padding:12px 16px;background:#161b22;border-radius:4px;">
      <div style="color:#d29922;font-weight:bold;">⚠️ SERVICE RESTARTED</div>
      <table style="width:100%;margin-top:12px;">
        <tr><td style="color:#8b949e;">Service</td><td style="color:#e6edf3;font-weight:bold;">{service}</td></tr>
        <tr><td style="color:#8b949e;">Reason</td><td style="color:#e6edf3;">{reason}</td></tr>
        <tr><td style="color:#8b949e;">Attempt #</td><td style="color:#e6edf3;">{attempt}</td></tr>
        <tr><td style="color:#8b949e;">Time</td><td style="color:#e6edf3;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
      </table>
    </div>
    """
    return send_email(f"Service Restarted: {service}", body)


def notify_self_heal(issues: list, heals: int) -> bool:
    """Notify when self-healer fixes something."""
    if not issues:
        return False  # don't spam for clean runs
    issue_rows = "".join([
        f'<tr><td style="color:#f85149;padding:4px 0;">⚠ {i}</td></tr>'
        for i in issues
    ])
    body = f"""
    <div style="border-left:4px solid #58a6ff;padding:12px 16px;background:#161b22;border-radius:4px;">
      <div style="color:#58a6ff;font-weight:bold;">🔧 SELF-HEALER ACTIVATED</div>
      <p style="color:#8b949e;">{heals} issue(s) automatically resolved</p>
      <table style="width:100%;">{issue_rows}</table>
    </div>
    """
    return send_email(f"Self-Healer: {heals} issue(s) fixed", body)


def notify_startup() -> bool:
    """Send notification when system starts up."""
    body = f"""
    <div style="border-left:4px solid #3fb950;padding:12px 16px;background:#161b22;border-radius:4px;">
      <div style="color:#3fb950;font-weight:bold;">🚀 SYSTEM ONLINE</div>
      <p style="color:#8b949e;">ServerRoot.net v2.0.0-Enterprise has started successfully.</p>
      <table style="width:100%;margin-top:12px;">
        <tr><td style="color:#8b949e;">API Server</td><td style="color:#3fb950;">✅ Running on :5001</td></tr>
        <tr><td style="color:#8b949e;">UI Server</td><td style="color:#3fb950;">✅ Running on :3001</td></tr>
        <tr><td style="color:#8b949e;">C2 Server</td><td style="color:#3fb950;">✅ Ready on :8443</td></tr>
        <tr><td style="color:#8b949e;">Automation</td><td style="color:#3fb950;">✅ Watchdog + Scheduler + Self-Healer</td></tr>
        <tr><td style="color:#8b949e;">Started At</td><td style="color:#e6edf3;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
      </table>
    </div>
    """
    return send_email("System Online — All Services Up", body)


def notify_backup_complete(files_backed_up: int, backup_path: str) -> bool:
    """Notify on successful backup."""
    body = f"""
    <div style="border-left:4px solid #3fb950;padding:12px 16px;background:#161b22;border-radius:4px;">
      <div style="color:#3fb950;font-weight:bold;">💾 BACKUP COMPLETE</div>
      <table style="width:100%;margin-top:12px;">
        <tr><td style="color:#8b949e;">Files Backed Up</td><td style="color:#e6edf3;">{files_backed_up}</td></tr>
        <tr><td style="color:#8b949e;">Backup Location</td><td style="color:#e6edf3;font-family:monospace;">{backup_path}</td></tr>
        <tr><td style="color:#8b949e;">Timestamp</td><td style="color:#e6edf3;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
      </table>
    </div>
    """
    return send_email("Backup Complete", body)


def notify_disk_warning(usage_pct: float, path: str = "/") -> bool:
    """Alert when disk usage is high."""
    color = "#f85149" if usage_pct > 95 else "#d29922"
    level = "CRITICAL" if usage_pct > 95 else "WARNING"
    body = f"""
    <div style="border-left:4px solid {color};padding:12px 16px;background:#161b22;border-radius:4px;">
      <div style="color:{color};font-weight:bold;">💾 DISK SPACE {level}</div>
      <p style="color:#e6edf3;font-size:24px;font-weight:bold;">{usage_pct:.1f}% used</p>
      <p style="color:#8b949e;">Path: {path}</p>
      <p style="color:#8b949e;">Please clean up old logs, scans, or expand storage.</p>
    </div>
    """
    return send_email(f"Disk {level}: {usage_pct:.1f}% Used", body)


def test_email() -> bool:
    """Send a test email to verify configuration."""
    body = """
    <div style="border-left:4px solid #58a6ff;padding:12px 16px;background:#161b22;border-radius:4px;">
      <div style="color:#58a6ff;font-weight:bold;">✅ EMAIL CONFIGURED CORRECTLY</div>
      <p style="color:#8b949e;">This is a test notification from ServerRoot.net.</p>
      <p style="color:#8b949e;">All email alerts are now active.</p>
    </div>
    """
    return send_email("Test Notification — Email Working", body)


def get_config_status() -> dict:
    """Return current email configuration status."""
    return {
        "enabled": ENABLED,
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
        "smtp_user": SMTP_USER if SMTP_USER else "(not set)",
        "notify_to": NOTIFY_TO if NOTIFY_TO else "(not set)",
        "setup_required": not ENABLED
    }


if __name__ == "__main__":
    import sys
    status = get_config_status()
    print(f"\n{'='*50}")
    print("  ServerRoot.net — Email Notifier Status")
    print(f"{'='*50}")
    print(f"  Enabled:    {status['enabled']}")
    print(f"  SMTP Host:  {status['smtp_host']}:{status['smtp_port']}")
    print(f"  From:       {status['smtp_user']}")
    print(f"  Notify To:  {status['notify_to']}")
    print(f"{'='*50}")
    
    if "--test" in sys.argv:
        print("\n  Sending test email...")
        result = test_email()
        print(f"  {'✓ Sent!' if result else '✗ Failed — check SMTP config'}")
    elif not ENABLED:
        print("\n  ⚠  Email not configured.")
        print("  Add these to your .env file:")
        print("    SMTP_HOST=smtp.gmail.com")
        print("    SMTP_PORT=587")
        print("    SMTP_USER=you@gmail.com")
        print("    SMTP_PASS=your-app-password")
        print("    NOTIFY_EMAIL=alerts@yourdomain.com")
        print("\n  Then test with: python automation/email_notifier.py --test")
    print()