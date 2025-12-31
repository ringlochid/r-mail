import click
import sys
import markdown
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rmail.database import get_db, query_db, APP_DIR  # Import APP_DIR
from rmail import engine

console = Console()

@click.command(name='send')
@click.option('-f', '--from', 'sender_alias', required=True, help='Sender alias')
@click.option('-t', '--to', 'receiver_input', required=True, help='Receiver alias OR email')
@click.option('-s', '--subject', required=True, help='Email Subject')
@click.option('-b', '--body', help='HTML Body (overrides template)')
@click.option('-p', '--template', help='Template filename')
@click.option('-S', '--set', 'context_vars', multiple=True, help='Context variable (key=value)')
@click.option('-a', '--attach', multiple=True, help='Attachment path')
@click.option('--editor/--no-editor', default=True, help='Open editor if no body provided')
def send_cmd(sender_alias, receiver_input, subject, body, template, context_vars, attach, editor):
    """Send an email. Opens Vim for body if no args provided."""

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

    context = {"name": receiver_name, "email": receiver_email}
    for item in context_vars:
        try:
            key, val = item.split('=', 1)
            context[key] = val
        except ValueError:
            pass

    final_body = ""
    if body:
        final_body = body
    elif template:
        # Smart Extension Detection
        tpl_name = template
        tpl_dir = APP_DIR / "templates"

        # If user didn't type an extension, check what exists
        if not (tpl_name.endswith('.html') or tpl_name.endswith('.md')):
            if (tpl_dir / f"{tpl_name}.md").exists():
                tpl_name += '.md'
            elif (tpl_dir / f"{tpl_name}.html").exists():
                tpl_name += '.html'
            else:
                # Default fallback (so the error message says .html)
                tpl_name += '.html'

        try:
            final_body = engine.render_template(tpl_name, context)
        except Exception as e:
            console.print(f"[bold red]Template Error:[/bold red] {e}")
            return

    else:
        # Interactive Mode (Vim)
        if sys.stdin.isatty() and editor:
            console.print("[yellow]Opening Vim for Markdown composition...[/yellow]")
            marker = f"# Message to {receiver_email}\n\n"
            input_text = click.edit(marker, extension=".md")

            if input_text is None:
                console.print("[red]Aborted: No message saved.[/red]")
                return

            final_body = markdown.markdown(input_text)

            console.print(Panel(final_body, title="Preview (HTML Rendered)"))
            if not click.confirm("Send this email?"):
                return
        else:
            final_body = sys.stdin.read() if not sys.stdin.isatty() else "<p>Empty</p>"

    # Send Logic
    try:
        console.print(f"[dim]Sending from {sender_row['email']} to {receiver_email}...[/dim]")
        engine.send_email(sender_row, receiver_email, subject, final_body, attach)
        console.print(f"[bold green]✔ Email sent successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to send:[/bold red] {e}")
