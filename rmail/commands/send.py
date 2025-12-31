import click
import sys
import markdown
from rich.console import Console
from rich.panel import Panel
from rmail.database import get_db, query_db
from rmail import engine

console = Console()

@click.command(name='send')
@click.option('-f', '--from', 'sender_alias', prompt=True, required=True, help='Sender alias')
@click.option('-t', '--to', 'receiver_input', prompt=True, required=True, help='Receiver alias OR email')
@click.option('-s', '--subject', prompt=True, required=True, help='Email Subject')
@click.option('-b', '--body', help='HTML Body (overrides template)')
@click.option('-p', '--template', help='Template filename')
@click.option('-S', '--set', 'context_vars', multiple=True, help='Context variable (key=value)')
@click.option('-a', '--attach', multiple=True, help='Attachment path')
@click.option('--editor/--no-editor', default=True, help='Open editor if no body provided')
def send_cmd(sender_alias, receiver_input, subject, body, template, context_vars, attach, editor):
    """Send an email. Opens Vim for body if no args provided."""

    # ... [Resolution Logic for Sender/Receiver is same as before] ...
    # (Copy the SQL query parts from your previous file here to save space)
    # ---------------------------------------------------------
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
    # ---------------------------------------------------------

    final_body = ""

    # 1. Parse Context Variables
    context = {"name": receiver_name, "email": receiver_email}
    for item in context_vars:
        try:
            key, val = item.split('=', 1)
            context[key] = val
        except ValueError:
            pass

    # 2. Determine Body Source
    if body:
        final_body = body
    elif template:
        if not template.endswith('.html'):
            template += '.html'
        final_body = engine.render_template(template, context)
    else:
        # Interactive Mode!
        if sys.stdin.isatty() and editor:
            console.print("[yellow]Opening Vim for Markdown composition...[/yellow]")
            # Pre-fill with a header
            marker = f"# Message to {receiver_email}\n\n"
            input_text = click.edit(marker, extension=".md")

            if input_text is None:
                console.print("[red]Aborted: No message saved.[/red]")
                return

            # Remove the marker line if it exists
            # Convert Markdown to HTML
            final_body = markdown.markdown(input_text)

            console.print(Panel(final_body, title="Preview (HTML Rendered)"))
            if not click.confirm("Send this email?"):
                return
        else:
            final_body = sys.stdin.read() if not sys.stdin.isatty() else "<p>Empty</p>"

    # 3. Send
    try:
        console.print(f"[dim]Sending from {sender_row['email']} to {receiver_email}...[/dim]")
        engine.send_email(sender_row, receiver_email, subject, final_body, attach)
        console.print(f"[bold green]✔ Email sent successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to send:[/bold red] {e}")
