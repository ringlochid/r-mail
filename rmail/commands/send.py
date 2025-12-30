import click
import sys
from rich.console import Console
from rmail.database import get_db, query_db
from rmail import engine

console = Console()

@click.command(name='send')
@click.option('-f', '--from', 'sender_alias', required=True, help='Sender alias (e.g., "myself")')
@click.option('-t', '--to', 'receiver_input', required=True, help='Receiver alias OR email address')
@click.option('-s', '--subject', required=True, help='Email Subject')
@click.option('-b', '--body', help='HTML Body content (or pass via stdin)')
@click.option('-a', '--attach', multiple=True, help='Path to attachment file')
def send_cmd(sender_alias, receiver_input, subject, body, attach):
    """Send an email using a configured identity."""

    # 1. Resolve Sender
    sql = """
        SELECT s.email, s.fullname, d.name as domain_name, d.smtp_host, d.smtp_port, d.smtp_user, d.security
        FROM senders s
        JOIN domains d ON s.domain_id = d.id
        WHERE s.alias = ?
    """
    sender_row = query_db(sql, (sender_alias,), one=True)

    if not sender_row:
        console.print(f"[bold red]Error:[/bold red] Sender alias '{sender_alias}' not found.")
        return

    # 2. Resolve Receiver (Alias lookup vs Raw Email)
    if "@" not in receiver_input:
        # Assume it's an alias
        receiver_row = query_db("SELECT email FROM receivers WHERE alias = ?", (receiver_input,), one=True)
        if not receiver_row:
            console.print(f"[bold red]Error:[/bold red] Receiver alias '{receiver_input}' not found.")
            return
        receiver_email = receiver_row['email']
    else:
        # It's a raw email
        receiver_email = receiver_input

    # 3. Handle Body (Input vs Pipe)
    if not body:
        # Check if data is being piped (echo "hello" | r-mail send ...)
        if not sys.stdin.isatty():
            body = sys.stdin.read()
        else:
            console.print("[yellow]No body provided. Using default empty body.[/yellow]")
            body = "<p>Sent via r-mail</p>"

    # 4. Send
    try:
        console.print(f"[dim]Sending from {sender_row['email']} to {receiver_email}...[/dim]")
        engine.send_email(sender_row, receiver_email, subject, body, attach)
        console.print(f"[bold green]✔ Email sent successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to send:[/bold red] {e}")

