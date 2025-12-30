import click
from rich.console import Console
from rich.table import Table
from rmail.database import get_db, query_db

console = Console()

@click.group(name='receiver')
def receiver_bp():
    """Manage Receiver Address Book."""
    pass

@receiver_bp.command(name='add')
@click.option('--alias', prompt=True, help='Short alias (e.g., "client1")')
@click.option('--name', prompt=True, help='Full Name')
@click.option('--email', prompt=True, help='Email Address')
def add_receiver(alias, name, email):
    """Add a contact to the address book."""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO receivers (alias, name, email) VALUES (?, ?, ?)",
            (alias, name, email)
        )
        db.commit()
        console.print(f"[green]✔ Contact '{alias}' added successfully![/green]")
    except Exception as e:
        console.print(f"[bold red]Failed to add contact:[/bold red] {e}")

@receiver_bp.command(name='list')
def list_receivers():
    """List all contacts."""
    receivers = query_db("SELECT alias, name, email FROM receivers")

    if not receivers:
        console.print("[yellow]Address book is empty.[/yellow]")
        return

    table = Table(title="Address Book")
    table.add_column("Alias", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Email", style="magenta")

    for r in receivers:
        table.add_row(r['alias'], r['name'], r['email'])

    console.print(table)
