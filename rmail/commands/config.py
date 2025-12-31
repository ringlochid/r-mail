import click
import os
from pathlib import Path
from cryptography.fernet import Fernet
from rich.console import Console
from rich.panel import Panel

console = Console()

@click.group(name='config')
def config_bp():
    """Configuration utilities."""
    pass

@config_bp.command(name='setup-key')
def setup_key():
    """Generates a Master Key and saves it to ~/.bashrc."""

    # 1. Check if key already exists in environment
    if os.getenv("RMAIL_MASTER_KEY"):
        console.print("[yellow]RMAIL_MASTER_KEY is already set in your environment.[/yellow]")
        if not click.confirm("Do you want to generate a NEW one? (This will make old secrets unreadable)"):
            return

    # 2. Generate Key
    new_key = Fernet.generate_key().decode()
    export_cmd = f'\nexport RMAIL_MASTER_KEY="{new_key}"'

    # 3. Detect Shell Config
    shell = os.getenv("SHELL", "/bin/bash")
    rc_file = Path.home() / (".zshrc" if "zsh" in shell else ".bashrc")

    # 4. Append to file
    try:
        with open(rc_file, "a") as f:
            f.write(export_cmd)

        console.print(Panel(
            f"[green]✔ Key generated and added to {rc_file}[/green]\n\n"
            f"[bold]Key:[/bold] {new_key}\n\n"
            f"[bold red]ACTION REQUIRED:[/bold red] Run this command to apply changes now:\n"
            f"[bold white]source {rc_file}[/bold white]",
            title="Security Setup Complete"
        ))
    except Exception as e:
        console.print(f"[red]Failed to write to {rc_file}: {e}[/red]")
