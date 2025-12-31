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

@receiver_bp.command(name='update')
@click.argument('alias')
@click.option('--name', help='New Name')
@click.option('--email', help='New Email')
def update_receiver(alias, name, email):
    """Update a contact."""
    db = get_db()
    updates = []
    params = []

    if name:
        updates.append("name = ?")
        params.append(name)
    if email:
        updates.append("email = ?")
        params.append(email)

    if not updates:
        console.print("[yellow]No changes provided.[/yellow]")
        return

    params.append(alias)

    try:
        sql = f"UPDATE receivers SET {', '.join(updates)} WHERE alias = ?"
        cur = db.execute(sql, params)
        db.commit()
        if cur.rowcount == 0:
            console.print(f"[red]Contact '{alias}' not found.[/red]")
        else:
            console.print(f"[green]✔ Contact '{alias}' updated.[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@receiver_bp.command(name='delete')
@click.argument('alias')
@click.confirmation_option(prompt='Delete this contact?')
def delete_receiver(alias):
    """Delete a contact."""
    db = get_db()
    try:
        cur = db.execute("DELETE FROM receivers WHERE alias = ?", (alias,))
        db.commit()
        if cur.rowcount > 0:
            console.print(f"[green]✔ Contact '{alias}' deleted.[/green]")
        else:
            console.print(f"[red]Contact '{alias}' not found.[/red]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@receiver_bp.command(name='list')
@click.argument('query', required=False)
def list_receivers(query):
    """List contacts. Optional: filter by query."""
    sql = "SELECT alias, name, email FROM receivers"
    params = ()

    if query:
        sql += " WHERE alias LIKE ? OR name LIKE ? OR email LIKE ?"
        wildcard = f"%{query}%"
        params = (wildcard, wildcard, wildcard)

    receivers = query_db(sql, params)

    if not receivers:
        console.print("[yellow]Address book is empty or no matches found.[/yellow]")
        return

    table = Table(title=f"Address Book {'(Filtered)' if query else ''}")
    table.add_column("Alias", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Email", style="magenta")

    for r in receivers:
        table.add_row(r['alias'], r['name'], r['email'])

    console.print(table)
