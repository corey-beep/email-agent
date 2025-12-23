"""
Email agent that combines email client with LLM capabilities.
"""

from dataclasses import dataclass
from typing import Optional
from email_client import EmailClient, Email
from llm_client import LLMClient
from config import agent_config


@dataclass
class EmailSummary:
    """Summary of an email with AI-generated insights."""
    email: Email
    summary: str
    category: str
    action_items: str
    priority: str


class EmailAgent:
    """AI-powered email agent for managing your inbox."""

    def __init__(self):
        self.email_client = EmailClient()
        self.llm = LLMClient()
        self.config = agent_config

    def check_connections(self) -> dict:
        """Check if all services are connected."""
        email_ok = self.email_client.connect()
        llm_ok = self.llm.check_connection()
        self.email_client.disconnect()

        return {
            "email": email_ok,
            "llm": llm_ok,
            "ready": email_ok and llm_ok
        }

    def get_inbox_summary(self, limit: int = None, unread_only: bool = True) -> list[EmailSummary]:
        """Get a summary of recent emails."""
        limit = limit or self.config.max_emails_to_fetch
        summaries = []

        with self.email_client as client:
            emails = client.fetch_emails(limit=limit, unread_only=unread_only)

            for email in emails:
                summary = EmailSummary(
                    email=email,
                    summary=self.llm.summarize(
                        f"Subject: {email.subject}\n\n{email.body}",
                        max_words=self.config.summary_max_words
                    ),
                    category=self.llm.categorize(email.subject, email.body),
                    action_items=self.llm.extract_action_items(email.body),
                    priority=self._determine_priority(email)
                )
                summaries.append(summary)

        return summaries

    def _determine_priority(self, email: Email) -> str:
        """Determine email priority based on content."""
        prompt = f"""Rate the priority of this email as HIGH, MEDIUM, or LOW.
Consider urgency, sender importance, and deadlines.
Only respond with one word: HIGH, MEDIUM, or LOW.

Subject: {email.subject}
From: {email.sender}

{email.body[:500]}"""

        response = self.llm.chat(prompt).strip().upper()

        if "HIGH" in response:
            return "HIGH"
        elif "LOW" in response:
            return "LOW"
        return "MEDIUM"

    def draft_reply(self, email: Email, instructions: str = None) -> str:
        """Draft a reply to an email."""
        return self.llm.draft_reply(email.subject, email.body, instructions)

    def process_email(self, email: Email) -> EmailSummary:
        """Fully process a single email."""
        return EmailSummary(
            email=email,
            summary=self.llm.summarize(
                f"Subject: {email.subject}\n\n{email.body}",
                max_words=self.config.summary_max_words
            ),
            category=self.llm.categorize(email.subject, email.body),
            action_items=self.llm.extract_action_items(email.body),
            priority=self._determine_priority(email)
        )

    def organize_inbox(self, dry_run: bool = True) -> list[dict]:
        """Organize emails by moving them to appropriate folders."""
        results = []

        with self.email_client as client:
            emails = client.fetch_emails(limit=self.config.max_emails_to_fetch)
            folders = client.get_folders()

            for email in emails:
                category = self.llm.categorize(email.subject, email.body)

                # Find matching folder (case-insensitive)
                target_folder = None
                for folder in folders:
                    if category.lower() in folder.lower():
                        target_folder = folder
                        break

                action = {
                    "email_id": email.id,
                    "subject": email.subject,
                    "category": category,
                    "target_folder": target_folder,
                    "moved": False
                }

                if target_folder and not dry_run:
                    action["moved"] = client.move_email(email.id, target_folder)

                results.append(action)

        return results

    def get_daily_digest(self) -> str:
        """Generate a daily digest of your inbox."""
        summaries = self.get_inbox_summary(unread_only=True)

        if not summaries:
            return "No unread emails to summarize."

        digest_parts = [f"# Daily Email Digest\n\nYou have {len(summaries)} unread email(s).\n"]

        # Group by priority
        high = [s for s in summaries if s.priority == "HIGH"]
        medium = [s for s in summaries if s.priority == "MEDIUM"]
        low = [s for s in summaries if s.priority == "LOW"]

        if high:
            digest_parts.append("\n## High Priority\n")
            for s in high:
                digest_parts.append(self._format_summary(s))

        if medium:
            digest_parts.append("\n## Medium Priority\n")
            for s in medium:
                digest_parts.append(self._format_summary(s))

        if low:
            digest_parts.append("\n## Low Priority\n")
            for s in low:
                digest_parts.append(self._format_summary(s))

        # Collect all action items
        all_actions = []
        for s in summaries:
            if "no action" not in s.action_items.lower():
                all_actions.append(f"From '{s.email.subject}':\n{s.action_items}")

        if all_actions:
            digest_parts.append("\n## All Action Items\n")
            digest_parts.extend(all_actions)

        return "\n".join(digest_parts)

    def _format_summary(self, summary: EmailSummary) -> str:
        """Format an email summary for display."""
        return f"""
**{summary.email.subject}**
From: {summary.email.sender}
Category: {summary.category}

{summary.summary}

---
"""
