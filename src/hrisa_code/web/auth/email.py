"""Email service for sending magic links and other notifications."""

import os
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        app_base_url: str,
    ):
        """Initialize email service.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port (typically 587 for TLS)
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: Email address to send from
            app_base_url: Base URL of the application (e.g., https://hrisa.example.com)
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.app_base_url = app_base_url.rstrip("/")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject

            # Add plain text version if provided
            if text_body:
                part1 = MIMEText(text_body, "plain")
                message.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_body, "html")
            message.attach(part2)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_magic_link(
        self,
        to_email: str,
        token: str,
        is_new_user: bool = False,
    ) -> bool:
        """Send a magic link email to a user.

        Args:
            to_email: Recipient email address
            token: Magic link token
            is_new_user: Whether this is a new user (first login)

        Returns:
            True if email sent successfully, False otherwise
        """
        magic_link = f"{self.app_base_url}/auth/verify?token={token}"

        # Determine subject and greeting based on user status
        if is_new_user:
            subject = "Welcome to Hrisa Code - Your Login Link"
            greeting = "Welcome to Hrisa Code!"
            intro_text = "We're excited to have you on board. Click the button below to complete your registration and access your account."
        else:
            subject = "Your Hrisa Code Login Link"
            greeting = "Welcome back!"
            intro_text = "Click the button below to securely log in to your account."

        # HTML email template with Material Design styling
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">
                                Hrisa Code
                            </h1>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #1a202c; font-size: 24px; font-weight: 600;">
                                {greeting}
                            </h2>

                            <p style="margin: 0 0 24px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                {intro_text}
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" style="margin: 30px 0;">
                                <tr>
                                    <td style="text-align: center;">
                                        <a href="{magic_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); transition: all 0.3s ease;">
                                            Log In to Hrisa Code
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 24px 0 0 0; color: #718096; font-size: 14px; line-height: 1.6;">
                                This link will expire in <strong>15 minutes</strong> and can only be used once.
                            </p>

                            <p style="margin: 16px 0 0 0; color: #718096; font-size: 14px; line-height: 1.6;">
                                If the button doesn't work, copy and paste this link into your browser:
                            </p>

                            <div style="margin: 12px 0 0 0; padding: 12px; background: #f7fafc; border-radius: 6px; border-left: 3px solid #667eea; word-break: break-all;">
                                <a href="{magic_link}" style="color: #667eea; text-decoration: none; font-size: 13px;">
                                    {magic_link}
                                </a>
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background: #f7fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 8px 0; color: #718096; font-size: 13px;">
                                If you didn't request this login link, you can safely ignore this email.
                            </p>
                            <p style="margin: 0; color: #a0aec0; font-size: 12px;">
                                &copy; 2024 Hrisa Code. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

        # Plain text fallback
        text_body = f"""
{greeting}

{intro_text}

Click this link to log in:
{magic_link}

This link will expire in 15 minutes and can only be used once.

If you didn't request this login link, you can safely ignore this email.

---
Hrisa Code
"""

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )


def create_email_service_from_env() -> Optional[EmailService]:
    """Create EmailService from environment variables.

    Required environment variables:
        - SMTP_HOST: SMTP server hostname
        - SMTP_PORT: SMTP server port
        - SMTP_USER: SMTP username
        - SMTP_PASSWORD: SMTP password
        - SMTP_FROM_EMAIL: Email address to send from
        - APP_BASE_URL: Base URL of the application

    Returns:
        EmailService instance if all env vars are set, None otherwise
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")
    app_base_url = os.getenv("APP_BASE_URL")

    if not all([smtp_host, smtp_port, smtp_user, smtp_password, from_email, app_base_url]):
        logger.warning("Email service not configured - missing required environment variables")
        return None

    try:
        smtp_port_int = int(smtp_port)
    except ValueError:
        logger.error(f"Invalid SMTP_PORT value: {smtp_port}")
        return None

    return EmailService(
        smtp_host=smtp_host,
        smtp_port=smtp_port_int,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        from_email=from_email,
        app_base_url=app_base_url,
    )
