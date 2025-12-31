import click
from rich.console import Console
from rich.table import Table
from rmail.database import get_db, query_db

console = Console()

@click.group(name='sender')
def sender_bp():
    """Manage Sender Identities (From addresses)."""
    pass

@sender_bp.command(name='add')
@click.option('--alias', prompt=True, help='Short alias (e.g., "me", "work")')
@click.option('--name', prompt=True, help='Full Name (e.g., "John Doe")')
@click.option('--email', prompt=True, help='Email Address')
@click.option('--domain', prompt=True, help='Name of the Domain to use (must exist)')
def add_sender(alias, name, email, domain):
    """Create a new sender identity."""
    db = get_db()

    # Verify Domain Exists
    domain_record = query_db("SELECT id FROM domains WHERE name = ?", (domain,), one=True)
    if not domain_record:
        console.print(f"[bold red]Error:[/bold red] Domain '{domain}' not found.")
        return

    try:
        db.execute(
            "INSERT INTO senders (alias, fullname, email, domain_id) VALUES (?, ?, ?, ?)",
            (alias, name, email, domain_record['id'])
        )
        db.commit()
        console.print(f"[green]✔ Sender '{alias}' added successfully![/green]")
    except Exception as e:
        console.print(f"[bold red]Failed to add sender:[/bold red] {e}")

@sender_bp.command(name='update')
@click.argument('alias')
@click.option('--name', help='New Full Name')
@click.option('--email', help='New Email Address')
@click.option('--domain', help='New Domain Name')
def update_sender(alias, name, email, domain):
    """Update an existing sender identity."""
    db = get_db()

    # Build query dynamically
    updates = []
    params = []

    if name:
        updates.append("fullname = ?")
        params.append(name)
    if email:
        updates.append("email = ?")
        params.append(email)
    if domain:
        domain_record = query_db("SELECT id FROM domains WHERE name = ?", (domain,), one=True)
        if not domain_record:
            console.print(f"[bold red]Error:[/bold red] Domain '{domain}' not found.")
            return
        updates.append("domain_id = ?")
        params.append(domain_record['id'])

    if not updates:
        console.print("[yellow]No changes provided.[/yellow]")
        return

    params.append(alias) # For the WHERE clause

    try:
        sql = f"UPDATE senders SET {', '.join(updates)} WHERE alias = ?"
        cur = db.execute(sql, params)
        db.commit()

        if cur.rowcount == 0:
            console.print(f"[red]Sender alias '{alias}' not found.[/red]")
        else:
            console.print(f"[green]✔ Sender '{alias}' updated.[/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@sender_bp.command(name='delete')
@click.argument('alias')
@click.confirmation_option(prompt='Are you sure you want to delete this sender?')
def delete_sender(alias):
    """Delete a sender identity."""
    db = get_db()
    try:
        cur = db.execute("DELETE FROM senders WHERE alias = ?", (alias,))
        db.commit()
        if cur.rowcount > 0:
            console.print(f"[green]✔ Sender '{alias}' deleted.[/green]")
        else:
            console.print(f"[red]Sender '{alias}' not found.[/red]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@sender_bp.command(name='list')
@click.argument('query', required=False)
def list_senders(query):
    """List senders. Optional: filter by query."""
    sql = """
        SELECT s.alias, s.fullname, s.email, d.name as domain_name
        FROM senders s
        JOIN domains d ON s.domain_id = d.id
    """
    params = ()

    if query:
        sql += " WHERE s.alias LIKE ? OR s.fullname LIKE ? OR s.email LIKE ?"
        wildcard = f"%{query}%"
        params = (wildcard, wildcard, wildcard)

    senders = query_db(sql, params)

    if not senders:
        console.print("[yellow]No senders found.[/yellow]")
        return

    table = Table(title=f"Sender Identities {'(Filtered)' if query else ''}")
    table.add_column("Alias", style="cyan")
    table.add_column("From Header", style="green")
    table.add_column("Linked Domain", style="magenta")

    for s in senders:
        full_header = f"{s['fullname']} <{s['email']}>"
        table.add_row(s['alias'], full_header, s['domain_name'])

    console.print(table)
