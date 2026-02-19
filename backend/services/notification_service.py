import aiosmtplib
from email.message import EmailMessage
from config import settings

class NotificationService:
    @staticmethod
    async def send_email(to_email: str, subject: str, body: str):
        """
        Sends a real email using aiosmtplib.
        """
        if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
            print(f"DEBUG (MOCK EMAIL): To: {to_email}, Sub: {subject}, Body: {body}")
            return

        message = EmailMessage()
        message["From"] = settings.MAIL_FROM
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.MAIL_SERVER,
                port=settings.MAIL_PORT,
                username=settings.MAIL_USERNAME,
                password=settings.MAIL_PASSWORD,
                use_tls=True,
            )
            print(f"DEBUG: Email sent to {to_email}")
        except Exception as e:
            print(f"DEBUG: Failed to send email: {e}")

    @staticmethod
    async def send_push(user_id: int, message: str):
        """
        Mock for Push Notifications (OneSignal/Firebase)
        """
        print(f"DEBUG (PUSH): User {user_id} - {message}")

