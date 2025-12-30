import click
import os
from rich.console import Console
from rich.panel import Panel
from rmail import database

# Initialize Rich console for pretty output
console = Console()

@click.group()
def cli():
    """r-mail: The headless professional email CLI."""
    pass

@cli.command()
def init():
    """Initialize the database and secure vault permissions."""
    try:
        database.init_app()
        console.print("[green]✔ Database initialized successfully.[/green]")
        console.print(f"[dim]Location: {database.APP_DIR}[/dim]")

        # Check for Master Key
        if not os.getenv("RMAIL_MASTER_KEY"):
            from cryptography.fernet import Fernet
            new_key = Fernet.generate_key().decode()
            console.print(Panel(
                f"[bold red]MISSING MASTER KEY![/bold red]\n\n"
                f"You must set this environment variable to use the Vault:\n"
                f"[bold yellow]export RMAIL_MASTER_KEY='{new_key}'[/bold yellow]\n\n"
                f"Add this to your [bold]~/.bashrc[/bold] or [bold]~/.zshrc[/bold] now.",
                title="Security Warning"
            ))
    except Exception as e:
        console.print(f"[bold red]Error initializing:[/bold red] {e}")

# Lazy import commands to avoid circular dependencies
from rmail.commands.domain import domain_bp
from rmail.commands.sender import sender_bp
from rmail.commands.receiver  import receiver_bp
from rmail.commands.send import send_cmd
from rmail.commands.template import template_bp

cli.add_command(domain_bp)
cli.add_command(sender_bp)
cli.add_command(receiver_bp)
cli.add_command(send_cmd)
cli.add_command(template_bp)
