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

    # 1. Verify Domain Exists
    domain_record = query_db("SELECT id FROM domains WHERE name = ?", (domain,), one=True)
    if not domain_record:
        console.print(f"[bold red]Error:[/bold red] Domain '{domain}' not found. Add it with 'r-mail domain add' first.")
        return

    try:
        # 2. Insert Sender
        db.execute(
            "INSERT INTO senders (alias, fullname, email, domain_id) VALUES (?, ?, ?, ?)",
            (alias, name, email, domain_record['id'])
        )
        db.commit()
        console.print(f"[green]✔ Sender '{alias}' added successfully![/green]")
    except Exception as e:
        console.print(f"[bold red]Failed to add sender:[/bold red] {e}")

@sender_bp.command(name='list')
def list_senders():
    """List all sender identities."""
    # Join with domains to show which server they use
    sql = """
        SELECT s.alias, s.fullname, s.email, d.name as domain_name
        FROM senders s
        JOIN domains d ON s.domain_id = d.id
    """
    senders = query_db(sql)

    if not senders:
        console.print("[yellow]No senders configured.[/yellow]")
        return

    table = Table(title="Sender Identities")
    table.add_column("Alias", style="cyan")
    table.add_column("From Header", style="green")
    table.add_column("Linked Domain", style="magenta")

    for s in senders:
        full_header = f"{s['fullname']} <{s['email']}>"
        table.add_row(s['alias'], full_header, s['domain_name'])

    console.print(table)
