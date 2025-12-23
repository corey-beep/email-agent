#!/usr/bin/env python3
"""
Email Agent CLI - AI-powered email assistant using local LLMs.
"""

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from agent import EmailAgent

console = Console()


def print_header():
    """Print the application header."""
    console.print(Panel.fit(
        "[bold blue]Email Agent[/bold blue]\n"
        "[dim]AI-powered email assistant using local LLMs[/dim]",
        border_style="blue"
    ))


def check_status(agent: EmailAgent):
    """Check connection status."""
    console.print("\n[yellow]Checking connections...[/yellow]")
    status = agent.check_connections()

    table = Table(show_header=False)
    table.add_column("Service", style="bold")
    table.add_column("Status")

    email_status = "[green]Connected[/green]" if status["email"] else "[red]Failed[/red]"
    llm_status = "[green]Connected[/green]" if status["llm"] else "[red]Failed[/red]"

    table.add_row("Email (IMAP)", email_status)
    table.add_row("LLM (Ollama)", llm_status)

    console.print(table)

    if not status["ready"]:
        if not status["email"]:
            console.print("\n[red]Email connection failed. Check your .env configuration.[/red]")
        if not status["llm"]:
            console.print("\n[red]LLM connection failed. Is Ollama running?[/red]")
            console.print("[dim]Start Ollama with: ollama serve[/dim]")

    return status["ready"]


def show_digest(agent: EmailAgent):
    """Show daily email digest."""
    console.print("\n[yellow]Generating daily digest...[/yellow]\n")

    try:
        digest = agent.get_daily_digest()
        console.print(Markdown(digest))
    except Exception as e:
        console.print(f"[red]Error generating digest: {e}[/red]")


def show_inbox(agent: EmailAgent):
    """Show inbox summary."""
    unread_only = Confirm.ask("Show unread only?", default=True)
    limit = int(Prompt.ask("How many emails?", default="5"))

    console.print("\n[yellow]Fetching and analyzing emails...[/yellow]\n")

    try:
        summaries = agent.get_inbox_summary(limit=limit, unread_only=unread_only)

        if not summaries:
            console.print("[dim]No emails found.[/dim]")
            return

        for i, s in enumerate(summaries, 1):
            priority_color = {
                "HIGH": "red",
                "MEDIUM": "yellow",
                "LOW": "green"
            }.get(s.priority, "white")

            console.print(Panel(
                f"[bold]{s.email.subject}[/bold]\n"
                f"[dim]From: {s.email.sender}[/dim]\n"
                f"[dim]Date: {s.email.date}[/dim]\n\n"
                f"[bold]Summary:[/bold] {s.summary}\n\n"
                f"[bold]Category:[/bold] {s.category}\n"
                f"[bold]Action Items:[/bold]\n{s.action_items}",
                title=f"[{priority_color}]{s.priority}[/{priority_color}] Email {i}/{len(summaries)}",
                border_style=priority_color
            ))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def draft_reply_interactive(agent: EmailAgent):
    """Interactive reply drafting."""
    console.print("\n[yellow]Fetching recent emails...[/yellow]")

    with agent.email_client as client:
        emails = client.fetch_emails(limit=5)

        if not emails:
            console.print("[dim]No emails found.[/dim]")
            return

        table = Table(title="Recent Emails")
        table.add_column("#", style="bold")
        table.add_column("Subject")
        table.add_column("From")

        for i, email in enumerate(emails, 1):
            table.add_row(str(i), email.subject[:50], email.sender[:30])

        console.print(table)

        choice = Prompt.ask("Which email to reply to?", choices=[str(i) for i in range(1, len(emails)+1)])
        email = emails[int(choice) - 1]

        instructions = Prompt.ask("Any specific instructions? (or press Enter to skip)", default="")

        console.print("\n[yellow]Drafting reply...[/yellow]\n")
        reply = agent.draft_reply(email, instructions if instructions else None)

        console.print(Panel(reply, title="Draft Reply", border_style="green"))

        if Confirm.ask("Copy to clipboard?", default=False):
            try:
                import subprocess
                subprocess.run(['xclip', '-selection', 'clipboard'], input=reply.encode(), check=True)
                console.print("[green]Copied to clipboard![/green]")
            except:
                console.print("[dim]Clipboard copy not available[/dim]")


def organize_inbox(agent: EmailAgent):
    """Organize inbox by category."""
    dry_run = Confirm.ask("Dry run (preview only)?", default=True)

    console.print("\n[yellow]Analyzing emails for organization...[/yellow]\n")

    try:
        results = agent.organize_inbox(dry_run=dry_run)

        table = Table(title="Organization Results")
        table.add_column("Subject")
        table.add_column("Category")
        table.add_column("Target Folder")
        table.add_column("Status")

        for r in results:
            status = "[green]Moved[/green]" if r["moved"] else "[dim]Dry run[/dim]"
            if not r["target_folder"]:
                status = "[yellow]No folder match[/yellow]"

            table.add_row(
                r["subject"][:40],
                r["category"],
                r["target_folder"] or "-",
                status
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def clean_inbox(agent: EmailAgent):
    """Find and delete unimportant emails."""
    limit = int(Prompt.ask("How many emails to scan?", default="30"))

    console.print("\n[yellow]Analyzing emails for deletable content...[/yellow]")
    console.print("[dim]This may take a moment as each email is evaluated by the LLM.[/dim]\n")

    try:
        deletable = agent.find_deletable_emails(limit=limit)

        if not deletable:
            console.print("[green]No deletable emails found! Your inbox is clean.[/green]")
            return

        total_deletable = sum(len(emails) for emails in deletable.values())
        console.print(f"[yellow]Found {total_deletable} deletable email(s) from {len(deletable)} sender(s)[/yellow]\n")

        # Display grouped by sender
        sender_num = 0
        sender_map = {}

        for sender, emails in deletable.items():
            sender_num += 1
            sender_map[sender_num] = {"sender": sender, "emails": emails}

            table = Table(title=f"[bold]Sender {sender_num}:[/bold] {sender[:60]}", show_header=True)
            table.add_column("#", style="bold", width=4)
            table.add_column("Subject", width=40)
            table.add_column("Preview", width=50)

            for i, email_data in enumerate(emails, 1):
                table.add_row(
                    f"{sender_num}.{i}",
                    email_data["subject"][:40],
                    email_data["preview"][:50]
                )

            console.print(table)
            console.print("")

        # Action menu
        while True:
            console.print("[bold]Actions:[/bold]")
            console.print("  [cyan]<sender#>[/cyan]        - Delete all from that sender (e.g., '1')")
            console.print("  [cyan]<sender#.email#>[/cyan] - Delete single email (e.g., '1.2')")
            console.print("  [cyan]all[/cyan]             - Delete all deletable emails")
            console.print("  [cyan]done[/cyan]            - Exit cleanup")

            action = Prompt.ask("\nAction").strip().lower()

            if action == "done":
                break

            elif action == "all":
                if Confirm.ask(f"[red]Delete ALL {total_deletable} emails?[/red]", default=False):
                    deleted = 0
                    for sender_data in sender_map.values():
                        ids = [e["email"].id for e in sender_data["emails"]]
                        deleted += agent.delete_emails_from_sender(ids)
                    console.print(f"[green]Deleted {deleted} email(s)[/green]")
                    break

            elif "." in action:
                # Single email delete (e.g., "1.2")
                try:
                    sender_num, email_num = map(int, action.split("."))
                    if sender_num in sender_map:
                        emails = sender_map[sender_num]["emails"]
                        if 1 <= email_num <= len(emails):
                            email_data = emails[email_num - 1]
                            if Confirm.ask(f"Delete '{email_data['subject'][:40]}'?", default=True):
                                if agent.delete_email(email_data["email"].id):
                                    console.print("[green]Deleted![/green]")
                                    emails.pop(email_num - 1)
                                else:
                                    console.print("[red]Failed to delete[/red]")
                        else:
                            console.print("[red]Invalid email number[/red]")
                    else:
                        console.print("[red]Invalid sender number[/red]")
                except ValueError:
                    console.print("[red]Invalid format. Use sender#.email# (e.g., 1.2)[/red]")

            else:
                # Delete all from sender (e.g., "1")
                try:
                    sender_num = int(action)
                    if sender_num in sender_map:
                        sender_data = sender_map[sender_num]
                        count = len(sender_data["emails"])
                        if Confirm.ask(f"Delete all {count} email(s) from {sender_data['sender'][:40]}?", default=True):
                            ids = [e["email"].id for e in sender_data["emails"]]
                            deleted = agent.delete_emails_from_sender(ids)
                            console.print(f"[green]Deleted {deleted} email(s)[/green]")
                            del sender_map[sender_num]
                    else:
                        console.print("[red]Invalid sender number[/red]")
                except ValueError:
                    console.print("[red]Invalid input[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def main_menu():
    """Show main menu and handle user input."""
    agent = EmailAgent()

    print_header()

    if not check_status(agent):
        console.print("\n[red]Please fix connection issues before continuing.[/red]")
        sys.exit(1)

    while True:
        console.print("\n[bold]What would you like to do?[/bold]\n")
        console.print("1. Daily digest")
        console.print("2. Browse inbox")
        console.print("3. Draft a reply")
        console.print("4. Organize inbox")
        console.print("5. [red]Clean inbox[/red] (find & delete junk)")
        console.print("6. Check status")
        console.print("7. Exit")

        choice = Prompt.ask("\nChoice", choices=["1", "2", "3", "4", "5", "6", "7"])

        if choice == "1":
            show_digest(agent)
        elif choice == "2":
            show_inbox(agent)
        elif choice == "3":
            draft_reply_interactive(agent)
        elif choice == "4":
            organize_inbox(agent)
        elif choice == "5":
            clean_inbox(agent)
        elif choice == "6":
            check_status(agent)
        elif choice == "7":
            console.print("\n[dim]Goodbye![/dim]")
            break


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Goodbye![/dim]")
