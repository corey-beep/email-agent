# Email Agent

AI-powered email assistant using local LLMs (Ollama).

## Features

- **Daily Digest** - Summarize unread emails with priority ranking
- **Smart Categorization** - Automatically categorize emails
- **Action Item Extraction** - Pull out tasks from emails
- **Draft Replies** - AI-generated reply drafts
- **Inbox Organization** - Move emails to folders by category

## Requirements

- Python 3.10+
- Ollama running locally
- IMAP email account

## Setup

### 1. Install Ollama

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5:7b
ollama serve  # Keep running in background
```

### 2. Install Python dependencies

```bash
cd ~/Projects/email-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure email

```bash
cp .env.example .env
# Edit .env with your email settings
```

#### Common IMAP settings:

| Provider | IMAP Server | SMTP Server |
|----------|-------------|-------------|
| Gmail | imap.gmail.com | smtp.gmail.com |
| Outlook | outlook.office365.com | smtp.office365.com |
| Yahoo | imap.mail.yahoo.com | smtp.mail.yahoo.com |
| ProtonMail | 127.0.0.1 (Bridge) | 127.0.0.1 (Bridge) |
| Fastmail | imap.fastmail.com | smtp.fastmail.com |

**Note:** For Gmail/Outlook, you'll need an "App Password" not your regular password.

### 4. Run the agent

```bash
python main.py
```

## Usage

```
$ python main.py

┌──────────────────────────────────────┐
│           Email Agent                │
│  AI-powered email assistant          │
└──────────────────────────────────────┘

What would you like to do?

1. Daily digest
2. Browse inbox
3. Draft a reply
4. Organize inbox
5. Check status
6. Exit
```

## Project Structure

```
email-agent/
├── config.py        # Configuration management
├── email_client.py  # IMAP email client
├── llm_client.py    # Ollama LLM client
├── agent.py         # Main agent logic
├── main.py          # CLI entry point
├── requirements.txt
├── .env             # Your config (not committed)
└── .env.example     # Example config
```

## Customization

### Change the model

Edit `.env`:
```
OLLAMA_MODEL=mistral:7b
```

### Adjust summarization

Edit `.env`:
```
SUMMARY_MAX_WORDS=50
MAX_EMAILS=20
```

## Docker (Optional)

To containerize the agent code (Ollama runs on host):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

Run with:
```bash
docker build -t email-agent .
docker run -it --env-file .env --add-host=host.docker.internal:host-gateway email-agent
```

Set `OLLAMA_URL=http://host.docker.internal:11434` in `.env` when using Docker.

## License

MIT
