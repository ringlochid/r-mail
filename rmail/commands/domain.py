from sqlite3 import paramstyle
import click
import getpass
from rich.console import Console
from rich.table import Table
from rmail.database import get_db, query_db
from rmail.vault import Vault

console = Console()

@click.group(name='domain')
def domain_bp():
    """Manage SMTP Server configurations."""
    pass

@domain_bp.command(name='add')
@click.option('--name', prompt=True, help='Unique identifier (e.g., gmail-work)')
@click.option('--host', prompt=True, help='SMTP Host (e.g., smtp.gmail.com)')
@click.option('--port', prompt=True, type=int, default=587, help='SMTP Port')
@click.option('--user', prompt=True, help='SMTP Username/Email')
@click.option('--security', type=click.Choice(['STARTTLS', 'SSL', 'NONE']), default='STARTTLS', prompt=True)
def add_domain(name, host, port, user, security):
    """Add a new SMTP server configuration."""

    # 1. Capture Password Securely
    password = getpass.getpass(prompt=f"Enter SMTP Password for {user}: ")

    try:
        # 2. Save Metadata to SQLite
        db = get_db()
        db.execute(
            "INSERT INTO domains (name, smtp_host, smtp_port, smtp_user, security) VALUES (?, ?, ?, ?, ?)",
            (name, host, port, user, security)
        )
        db.commit()

        # 3. Save Password to Encrypted Vault
        vault = Vault()
        vault.set_password("rmail", name, password)

        console.print(f"[green]✔ Domain '{name}' added successfully![/green]")

    except Exception as e:
        console.print(f"[bold red]Failed to add domain:[/bold red] {e}")

@domain_bp.command(name='list')
@click.argument('query', required=False)
def list_domains(query):
    """List domains. Optional: filter by query"""
    domains = query_db("SELECT name, smtp_host, smtp_port, smtp_user, security FROM domains")

    sql = "SELECT name, smtp_host, smtp_port, smtp_user, security FROM domains "
    params = ()
    if query:
        sql += "WHERE name LIKE ? OR smtp_host LIKE ?"
        wildcard = f"%{query}%"
        params = (wildcard, wildcard)
    domains = query_db(sql, params)
    if not domains:
        console.print("[yellow]No domains configured.[/yellow]")
        return

    table = Table(title="SMTP Domains")
    table.add_column("Name", style="cyan")
    table.add_column("Host", style="magenta")
    table.add_column("User", style="green")
    table.add_column("Security")

    for domain in domains:
        table.add_row(domain['name'], f"{domain['smtp_host']}:{domain['smtp_port']}", domain['smtp_user'], domain['security'])

    console.print(table)

@domain_bp.command(name='delete')
@click.argument('name')
@click.confirmation_option(prompt='Delete this domain?')
def delete_domain(name):
    """Delete a domain (and remove password from Vault)."""
    db = get_db()

    # Check for usage first (Foreign Key constraint)
    usage = query_db("SELECT count(*) as c FROM senders WHERE domain_id = (SELECT id FROM domains WHERE name = ?)", (name,), one=True)
    if usage and usage['c'] > 0:
        console.print(f"[bold red]Cannot delete:[/bold red] Domain is used by {usage['c']} senders. Delete them first.")
        return

    try:
        # Delete from DB
        db.execute("DELETE FROM domains WHERE name = ?", (name,))
        db.commit()

        # Delete from Vault (ignore if missing)
        from rmail.vault import Vault
        try:
            Vault().set_password("rmail", name, None) # Or implement a delete method in Vault
        except:
            pass

        console.print(f"[green]✔ Domain '{name}' deleted.[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
