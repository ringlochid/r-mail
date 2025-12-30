import click
import sys
from rich.console import Console
from rmail.database import get_db, query_db
from rmail import engine

console = Console()

@click.command(name='send')
@click.option('-f', '--from', 'sender_alias', required=True, help='Sender alias')
@click.option('-t', '--to', 'receiver_input', required=True, help='Receiver alias OR email')
@click.option('-s', '--subject', required=True, help='Email Subject')
@click.option('-b', '--body', help='Raw HTML Body (overrides template)')
@click.option('-p', '--template', help='Template filename (e.g., welcome.html)')
@click.option('-S', '--set', 'context_vars', multiple=True, help='Context variable (key=value)')
@click.option('-a', '--attach', multiple=True, help='Attachment path')
def send_cmd(sender_alias, receiver_input, subject, body, template, context_vars, attach):
    """Send an email using a configured identity."""

    # 1. Resolve Sender (Same as before)
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

    # 2. Resolve Receiver (Same as before)
    if "@" not in receiver_input:
        receiver_row = query_db("SELECT email, name FROM receivers WHERE alias = ?", (receiver_input,), one=True)
        if not receiver_row:
            console.print(f"[bold red]Error:[/bold red] Receiver alias '{receiver_input}' not found.")
            return
        receiver_email = receiver_row['email']
        receiver_name = receiver_row['name']
    else:
        receiver_email = receiver_input
        receiver_name = ""

    # 3. Prepare Content
    final_body = ""

    # A. Parse Context Variables (-S name=John)
    context = {"name": receiver_name, "email": receiver_email} # Default context
    for item in context_vars:
        try:
            key, val = item.split('=', 1)
            context[key] = val
        except ValueError:
            console.print(f"[yellow]Warning: Ignoring invalid variable '{item}'. Use format key=value[/yellow]")

    # B. Determine Body Source
    if body:
        final_body = body
    elif template:
        try:
            # Ensure extension
            if not template.endswith('.html'):
                template += '.html'
            final_body = engine.render_template(template, context)
        except Exception as e:
            console.print(f"[bold red]Template Error:[/bold red] {e}")
            return
    else:
        # Fallback to Stdin
        if not sys.stdin.isatty():
            final_body = sys.stdin.read()
        else:
            final_body = "<p>Sent via r-mail</p>"

    # 4. Send
    try:
        console.print(f"[dim]Sending from {sender_row['email']} to {receiver_email}...[/dim]")
        engine.send_email(sender_row, receiver_email, subject, final_body, attach)
        console.print(f"[bold green]✔ Email sent successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to send:[/bold red] {e}")
