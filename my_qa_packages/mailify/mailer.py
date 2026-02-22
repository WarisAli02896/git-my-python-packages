import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import  MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional, Union

class Mailer:
    def __init__(
        self,
        smtp_server: str = None,
        port: int = 587,
        username: str = None,
        password: str = None,
        use_tls: bool = True,
        sender: str = None,
        config: dict = None
    ):
        # If connection configuration provided in config parameter then set all values in individual variables
        if config:
            smtp_server = config.get("smtp_server")
            port = config.get("port", 587)
            username = config.get("username")
            password = config.get("password")
            use_tls = config.get("use_tls", True)
            sender = config.get("sender")
        
        # Validation for checking all required values provided
        if not all([smtp_server, username, password, sender]):
            raise ValueError("Missing required mail configuration parameters: smtp_server, username, password, and sender are required")
        
        # Store configuration
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.sender = sender

    def send_mail(
        self,
        recipients: Union[str, List[str]],
        subject: str = "No Subject",
        body: str = "",
        attachments: Optional[List[str]] = None,
        html: bool = False,
    ):
        # Convert recipients to list if string
        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.split(",")]
        
        # Validate recipients
        if not recipients:
            raise ValueError("At least one recipient is required")
        
        msg = MIMEMultipart()
        msg["From"] = self.sender
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        # Attach body
        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body, mime_type))

        # Attach files if any
        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
                        msg.attach(part)
                except Exception as e:
                    print(f"Failed to attach {file_path}: {e}")

        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")
            raise