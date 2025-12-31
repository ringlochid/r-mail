import click
import json
from rich.console import Console
from rich.table import Table
from rmail.database import get_db, query_db

console = Console()

@click.group(name='context')
def context_bp():
    """Manage Context Profiles (Database backed)."""
    pass

@context_bp.command(name='add')
@click.argument('name')
@click.option('--description', help='Short description')
@click.option('--template', help='Linked Template filename (optional)')
def add_context(name, description, template):
    """Create a new context profile."""
    db = get_db()

    # 1. Open Vim to define the variables
    initial_data = {
        "variable_1": "value",
        "variable_2": "value"
    }

    msg = f"# Define variables for context '{name}' as JSON.\n" + json.dumps(initial_data, indent=4)
    result = click.edit(msg, extension=".json")

    if not result:
        console.print("[yellow]Aborted.[/yellow]")
        return

    # 2. Parse and Save
    try:
        # Strip comments
        clean_json = "\n".join([line for line in result.splitlines() if not line.strip().startswith("#")])
        json_data = json.loads(clean_json)

        db.execute(
            "INSERT INTO contexts (name, description, template_name, data) VALUES (?, ?, ?, ?)",
            (name, description, template, json.dumps(json_data))
        )
        db.commit()
        console.print(f"[green]✔ Context '{name}' created.[/green]")

    except json.JSONDecodeError:
        console.print("[bold red]Error:[/bold red] Invalid JSON format.")
    except Exception as e:
        console.print(f"[bold red]Database Error:[/bold red] {e}")

@context_bp.command(name='update')
@click.argument('name')
@click.option('--description', help='New Description')
@click.option('--template', help='New Linked Template')
def update_context(name, description, template):
    """Update metadata (Description/Template) for a context."""
    db = get_db()

    updates = []
    params = []

    if description is not None:
        updates.append("description = ?")
        params.append(description)

    if template is not None:
        updates.append("template_name = ?")
        params.append(template)

    if not updates:
        console.print("[yellow]No changes provided. Use --description or --template.[/yellow]")
        return

    params.append(name) # For WHERE clause

    try:
        sql = f"UPDATE contexts SET {', '.join(updates)} WHERE name = ?"
        cur = db.execute(sql, params)
        db.commit()

        if cur.rowcount > 0:
            console.print(f"[green]✔ Context '{name}' updated.[/green]")
        else:
            console.print(f"[red]Context '{name}' not found.[/red]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@context_bp.command(name='edit')
@click.argument('name')
def edit_context(name):
    """Edit the JSON variable data using Vim."""
    db = get_db()
    row = query_db("SELECT * FROM contexts WHERE name = ?", (name,), one=True)

    if not row:
        console.print(f"[red]Context '{name}' not found.[/red]")
        return

    # Load current data into Vim
    current_data = json.loads(row['data'])
    result = click.edit(json.dumps(current_data, indent=4), extension=".json")

    if not result:
        console.print("[yellow]No changes made.[/yellow]")
        return

    try:
        new_data = json.loads(result)
        db.execute("UPDATE contexts SET data = ? WHERE name = ?", (json.dumps(new_data), name))
        db.commit()
        console.print(f"[green]✔ Context '{name}' data updated.[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")

@context_bp.command(name='list')
@click.argument('query', required=False)
@click.option('--limit', default=10, help='Limit results')
@click.option('--offset', default=0, help='Pagination offset')
def list_contexts(query, limit, offset):
    """List contexts with pagination and search."""
    sql = "SELECT name, description, template_name, data FROM contexts"
    params = []

    if query:
        sql += " WHERE name LIKE ? OR template_name LIKE ?  OR description LIKE ?"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard,wildcard])

    sql += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = query_db(sql, params)

    if not rows:
        if query:
            console.print(f"[yellow]No contexts found matching '{query}'.[/yellow]")
        elif offset > 0:
            console.print("[yellow]No more contexts (end of list).[/yellow]")
        else:
            console.print("[yellow]No contexts found. Use 'r-mail context add' to create one.[/yellow]")
        return

    table = Table(title=f"Context Profiles {'(Filtered)' if query else ''}")
    table.add_column("Name", style="cyan")
    table.add_column("Linked Template", style="magenta")
    table.add_column("Description")
    table.add_column("Keys (Preview)", style="green")

    for r in rows:
        data = json.loads(r['data'])
        keys = ", ".join(list(data.keys())[:3])
        table.add_row(r['name'], r['template_name'] or "Any", r['description'] or "", keys)

    console.print(table)

@context_bp.command(name='delete')
@click.argument('name')
@click.confirmation_option(prompt="Are you sure?")
def delete_context(name):
    """Delete a context."""
    db = get_db()
    cur = db.execute("DELETE FROM contexts WHERE name = ?", (name,))
    db.commit()
    if cur.rowcount > 0:
        console.print(f"[green]✔ Deleted context '{name}'[/green]")
    else:
        console.print(f"[red]Context '{name}' not found.[/red]")
