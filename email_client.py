"""
IMAP email client for fetching and managing emails.
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from dataclasses import dataclass
from typing import Optional
from config import email_config


@dataclass
class Email:
    """Represents an email message."""
    id: str
    subject: str
    sender: str
    date: str
    body: str
    folder: str = "INBOX"
    flags: list = None

    def __post_init__(self):
        if self.flags is None:
            self.flags = []

    @property
    def is_unread(self) -> bool:
        return "\\Seen" not in self.flags


class EmailClient:
    """IMAP email client for fetching and managing emails."""

    def __init__(self):
        self.config = email_config
        self.imap: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> bool:
        """Connect to the IMAP server."""
        try:
            self.imap = imaplib.IMAP4_SSL(
                self.config.imap_server,
                self.config.imap_port
            )
            self.imap.login(self.config.email, self.config.password)
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """Disconnect from the IMAP server."""
        if self.imap:
            try:
                self.imap.logout()
            except:
                pass
            self.imap = None

    def _decode_header_value(self, value: str) -> str:
        """Decode an email header value."""
        if value is None:
            return ""
        decoded_parts = decode_header(value)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or "utf-8", errors="replace"))
            else:
                result.append(part)
        return " ".join(result)

    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract the body from an email message."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or "utf-8"
                        body = payload.decode(charset, errors="replace")
                        break
                    except:
                        continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace")
            except:
                body = str(msg.get_payload())
        return body.strip()

    def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False
    ) -> list[Email]:
        """Fetch emails from the specified folder."""
        if not self.imap:
            if not self.connect():
                return []

        emails = []
        try:
            self.imap.select(folder)

            search_criteria = "UNSEEN" if unread_only else "ALL"
            _, message_ids = self.imap.search(None, search_criteria)

            ids = message_ids[0].split()
            # Get most recent emails first
            ids = ids[-limit:] if len(ids) > limit else ids
            ids = list(reversed(ids))

            for msg_id in ids:
                _, msg_data = self.imap.fetch(msg_id, "(RFC822 FLAGS)")

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # Get flags
                        flags = []
                        flag_data = self.imap.fetch(msg_id, "(FLAGS)")
                        if flag_data[1] and flag_data[1][0]:
                            flag_str = flag_data[1][0].decode()
                            if "FLAGS" in flag_str:
                                start = flag_str.find("(", flag_str.find("FLAGS"))
                                end = flag_str.find(")", start)
                                if start != -1 and end != -1:
                                    flags = flag_str[start+1:end].split()

                        emails.append(Email(
                            id=msg_id.decode(),
                            subject=self._decode_header_value(msg["Subject"]),
                            sender=self._decode_header_value(msg["From"]),
                            date=msg["Date"] or "",
                            body=self._get_email_body(msg),
                            folder=folder,
                            flags=flags
                        ))

        except Exception as e:
            print(f"Error fetching emails: {e}")

        return emails

    def get_folders(self) -> list[str]:
        """Get list of available folders."""
        if not self.imap:
            if not self.connect():
                return []

        folders = []
        try:
            _, folder_list = self.imap.list()
            for folder_data in folder_list:
                if isinstance(folder_data, bytes):
                    # Parse folder name from response
                    parts = folder_data.decode().split(' "/" ')
                    if len(parts) >= 2:
                        folder_name = parts[-1].strip('"')
                        folders.append(folder_name)
        except Exception as e:
            print(f"Error getting folders: {e}")

        return folders

    def move_email(self, email_id: str, dest_folder: str) -> bool:
        """Move an email to a different folder."""
        if not self.imap:
            return False

        try:
            # Copy to destination
            self.imap.copy(email_id.encode(), dest_folder)
            # Mark as deleted in source
            self.imap.store(email_id.encode(), "+FLAGS", "\\Deleted")
            self.imap.expunge()
            return True
        except Exception as e:
            print(f"Error moving email: {e}")
            return False

    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read."""
        if not self.imap:
            return False

        try:
            self.imap.store(email_id.encode(), "+FLAGS", "\\Seen")
            return True
        except Exception as e:
            print(f"Error marking as read: {e}")
            return False

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email via SMTP."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.email
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.email, self.config.password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
