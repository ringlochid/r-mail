import click
import sys
import markdown
import json
from jinja2 import Environment
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rmail.database import get_db, query_db, APP_DIR
from rmail import engine

console = Console()

@click.command(name='send')
@click.option('-f', '--from', 'sender_alias', required=True, help='Sender alias')
@click.option('-t', '--to', 'receiver_input', required=True, help='Receiver alias OR email')
@click.option('-s', '--subject', help='Email Subject (Optional if in template)')
@click.option('-b', '--body', help='HTML Body (overrides template)')
@click.option('-p', '--template', help='Template filename')
@click.option('-M', '--message_file', type=click.File('r'), help='Load text file into {{ message_body }}')
@click.option('-S', '--set', 'context_vars', multiple=True, help='Context variable (key=value)')
@click.option('-C', '--context', 'context_profile', help='Load variables from a saved context profile')
@click.option('-a', '--attach', multiple=True, help='Attachment path')
@click.option('--editor/--no-editor', default=True, help='Open editor if no body provided')
def send_cmd(sender_alias, receiver_input, subject, body, template, message_file, context_vars, attach, editor, context_profile):
    """Send an email with smart template prompting."""
    # -------------------------------------------------------------
    # 1. Resolve Sender
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 2. Resolve Receiver
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 3. Prepare Content
    # -------------------------------------------------------------

    final_context = {"name": receiver_name, "email": receiver_email}

    # A. Layer 1: Load Saved Profile (Database)
    if context_profile:
        # NEW LOGIC: Query DB
        ctx_row = query_db("SELECT data FROM contexts WHERE name = ?", (context_profile,), one=True)

        if not ctx_row:
             console.print(f"[bold red]Error:[/bold red] Context profile '{context_profile}' not found.")
             return

        try:
            saved_data = json.loads(ctx_row['data'])
            final_context.update(saved_data)
            console.print(f"[dim]Loaded context '{context_profile}' from DB[/dim]")
        except Exception as e:
            console.print(f"[red]Error parsing context data:[/red] {e}")
            return

    if message_file:
        raw_content = message_file.read()
        if message_file.name.endswith('.md'):
            try:
                # Convert MD -> HTML so it's ready for ANY template
                html_content = markdown.markdown(raw_content)
                final_context['message_body'] = html_content
                console.print(f"[dim]Converted Markdown message from '{message_file.name}'[/dim]")
            except Exception as e:
                console.print(f"[bold red]Markdown Error:[/bold red] {e}")
                return
        else:
            # It's a plain text/html file, just pass it through
            final_context['message_body'] = raw_content
            console.print(f"[dim]Loaded message from '{message_file.name}'[/dim]")

    # B. Layer 2: Parse CLI Flags (Overwrites Profile)
    for item in context_vars:
        try:
            key, val = item.split('=', 1)
            final_context[key] = val
        except ValueError:
            pass

    final_body = ""

    # Logic: Template vs Body vs Interactive
    if body:
        final_body = body

    elif template:
        try:
            meta, raw_content, ext = engine.get_template_meta(template)

            if 'variables' in meta:
                missing_vars = [k for k in meta['variables'].keys() if k not in final_context]

                if missing_vars:
                    console.print(Panel(f"Template requires: {', '.join(meta['variables'].keys())}", title="Template Parameters", style="cyan"))

                    for var_name, description in meta['variables'].items():
                        # Layer 3: Interactive Prompt (Only if missing)
                        if var_name not in final_context:
                            user_val = click.prompt(f"{var_name} ({description})")
                            final_context[var_name] = user_val

            if not subject and 'subject' in meta:
                raw_subject = meta['subject']

                # Manually render the subject string
                env = Environment()
                subject_tmpl = env.from_string(raw_subject)
                subject = subject_tmpl.render(**final_context)

                console.print(f"[dim]Using subject: {subject}[/dim]")

            final_body = engine.render_template_content(raw_content, ext, final_context)

        except Exception as e:
            console.print(f"[bold red]Template Error:[/bold red] {e}")
            return

    else:
        # Interactive Vim Mode fallback
        if sys.stdin.isatty() and editor:
            console.print("[yellow]Opening Vim for Markdown composition...[/yellow]")
            marker = f"# Message to {receiver_email}\n\n"
            input_text = click.edit(marker, extension=".md")

            if input_text is None:
                console.print("[red]Aborted: No message saved.[/red]")
                return

            # Convert the interactive input to HTML
            final_body = markdown.markdown(input_text)

            if not subject:
                subject = click.prompt("Subject")
        else:
            final_body = sys.stdin.read() if not sys.stdin.isatty() else "<p>Empty</p>"

    # -------------------------------------------------------------
    # 4. Final Send
    # -------------------------------------------------------------
    if not subject:
        console.print("[red]Error: Subject is required.[/red]")
        return

    try:
        console.print(f"[dim]Sending from {sender_row['email']} to {receiver_email}...[/dim]")
        engine.send_email(sender_row, receiver_email, subject, final_body, attach)
        console.print(f"[bold green]✔ Email sent successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to send:[/bold red] {e}")
