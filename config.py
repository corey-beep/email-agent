"""
Configuration for the email agent.
Uses environment variables for sensitive data.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class EmailConfig:
    """IMAP email configuration."""
    imap_server: str = os.getenv("IMAP_SERVER", "")
    imap_port: int = int(os.getenv("IMAP_PORT", "993"))
    smtp_server: str = os.getenv("SMTP_SERVER", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    email: str = os.getenv("EMAIL_ADDRESS", "")
    password: str = os.getenv("EMAIL_PASSWORD", "")


@dataclass
class LLMConfig:
    """Ollama LLM configuration."""
    base_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))


@dataclass
class AgentConfig:
    """Agent behavior configuration."""
    max_emails_to_fetch: int = int(os.getenv("MAX_EMAILS", "10"))
    summary_max_words: int = int(os.getenv("SUMMARY_MAX_WORDS", "100"))


# Global config instances
email_config = EmailConfig()
llm_config = LLMConfig()
agent_config = AgentConfig()
