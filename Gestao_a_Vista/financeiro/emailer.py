from __future__ import annotations

from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


def save_email_draft_html(html: str, output_dir: Path, subject: str = "Alerta financeiro") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"rascunho_email_{stamp}.html"
    path.write_text(html, encoding="utf-8")
    return path


def save_email_draft_eml(html: str, output_dir: Path, to: str, subject: str = "Alerta financeiro") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("Seu cliente de e-mail nao exibiu HTML. Abra a versao HTML do rascunho.")
    msg.add_alternative(html, subtype="html")

    path = output_dir / f"rascunho_email_{stamp}.eml"
    path.write_bytes(bytes(msg))
    return path


def open_outlook_draft(to: str, subject: str, html: str) -> bool:
    try:
        import win32com.client  # type: ignore
    except Exception:
        return False

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = to
        mail.Subject = subject
        mail.HTMLBody = html
        mail.Display()
        return True
    except Exception:
        return False
