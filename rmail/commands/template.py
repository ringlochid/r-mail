import click
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rmail import database

console = Console()
TEMPLATE_DIR = database.APP_DIR / "templates"

@click.group(name='template')
def template_bp():
    """Manage Email Templates."""
    # Ensure template dir exists
    if not TEMPLATE_DIR.exists():
        TEMPLATE_DIR.mkdir(parents=True)

@template_bp.command(name='list')
def list_templates():
    """List available templates."""
    files = list(TEMPLATE_DIR.glob("*.html"))

    if not files:
        console.print("[yellow]No templates found. Create one with 'r-mail template edit <name>'[/yellow]")
        return

    table = Table(title="Email Templates")
    table.add_column("Filename", style="cyan")
    table.add_column("Size", style="green")

    for f in files:
        table.add_row(f.name, f"{f.stat().st_size} bytes")

    console.print(table)

@template_bp.command(name='edit')
@click.argument('name')
def edit_template(name):
    """Create or Edit a template using your default editor (nano, vim etc.)."""
    # Ensure extension
    if not name.endswith('.html'):
        name += '.html'

    file_path = TEMPLATE_DIR / name

    # If new file, create boilerplate
    if not file_path.exists():
        file_path.write_text("<h1>Hello {{ name }}</h1>\n<p>This is a new template.</p>")

    # Open Editor
    click.edit(filename=str(file_path))

    console.print(f"[green]✔ Template '{name}' saved.[/green]")

@template_bp.command(name='delete')
@click.argument('name')
@click.confirmation_option(prompt='Delete this template?')
def delete_template(name):
    """Delete a template."""
    if not name.endswith('.html'):
        name += '.html'

    file_path = TEMPLATE_DIR / name

    if file_path.exists():
        os.remove(file_path)
        console.print(f"[green]✔ Deleted {name}[/green]")
    else:
        console.print(f"[red]Template {name} not found.[/red]")
