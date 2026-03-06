import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.core.config import settings


class EmailService:
    """Service for sending emails via SMTP."""

    def send_email_with_attachment(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachment_bytes: bytes,
        attachment_filename: str,
        cc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email with a file attachment.
        
        Args:
            to_email: Recipient's email address
            subject: Email subject
            body: Email body (HTML supported)
            attachment_bytes: Bytes of the file to attach
            attachment_filename: Name of the file as it should appear in the email
            cc: Optional list of CC addresses
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create message container
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = to_email
            
            if settings.SMTP_REPLY_TO:
                msg["Reply-To"] = settings.SMTP_REPLY_TO

            if cc:
                msg["Cc"] = ", ".join(cc)
                recipients = [to_email] + cc
            else:
                recipients = [to_email]

            # Attach body
            msg.attach(MIMEText(body, "html"))

            # Attach PDF
            part = MIMEApplication(attachment_bytes, _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename=attachment_filename)
            msg.attach(part)

            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_PORT == 587:
                    server.starttls()
                
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                server.sendmail(settings.SMTP_FROM_EMAIL, recipients, msg.as_string())
            
            return True

        except Exception as e:
            # In a real app, we'd log this error
            print(f"Failed to send email: {e}")
            return False
