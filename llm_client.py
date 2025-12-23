"""
Ollama LLM client using OpenAI-compatible API.
"""

from openai import OpenAI
from config import llm_config


class LLMClient:
    """Client for interacting with local Ollama models."""

    def __init__(self):
        self.config = llm_config
        self.client = OpenAI(
            base_url=f"{self.config.base_url}/v1",
            api_key="ollama"  # Ollama doesn't need a real key
        )

    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """Send a chat message and get a response."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with LLM: {e}"

    def summarize(self, text: str, max_words: int = 100) -> str:
        """Summarize the given text."""
        system_prompt = """You are a helpful assistant that summarizes emails concisely.
Focus on: key points, action items, deadlines, and important details.
Be brief and use bullet points when appropriate."""

        prompt = f"""Summarize this email in {max_words} words or less:

{text}"""

        return self.chat(prompt, system_prompt)

    def draft_reply(self, email_subject: str, email_body: str, instructions: str = None) -> str:
        """Draft a reply to an email."""
        system_prompt = """You are a helpful assistant that drafts professional email replies.
Match the tone of the original email. Be concise but thorough.
Only output the reply body, no subject line or headers."""

        prompt = f"""Draft a reply to this email:

Subject: {email_subject}

{email_body}"""

        if instructions:
            prompt += f"\n\nAdditional instructions: {instructions}"

        return self.chat(prompt, system_prompt)

    def categorize(self, email_subject: str, email_body: str, categories: list[str] = None) -> str:
        """Categorize an email into a folder/label."""
        if categories is None:
            categories = ["Important", "Work", "Personal", "Newsletter", "Spam", "Other"]

        system_prompt = """You are a helpful assistant that categorizes emails.
Only respond with the category name, nothing else."""

        prompt = f"""Categorize this email into one of these categories: {", ".join(categories)}

Subject: {email_subject}

{email_body[:500]}

Category:"""

        response = self.chat(prompt, system_prompt)
        # Clean up response to just get the category
        response = response.strip().split("\n")[0]
        # Validate it's one of the categories
        for cat in categories:
            if cat.lower() in response.lower():
                return cat
        return "Other"

    def extract_action_items(self, email_body: str) -> str:
        """Extract action items from an email."""
        system_prompt = """You are a helpful assistant that extracts action items from emails.
List each action item on a new line starting with '- '.
If there are no action items, respond with 'No action items found.'"""

        prompt = f"""Extract all action items, tasks, or things that need to be done from this email:

{email_body}"""

        return self.chat(prompt, system_prompt)

    def check_connection(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            response = self.chat("Say 'OK' if you're working.")
            return "OK" in response.upper() or len(response) > 0
        except:
            return False
