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
    if not TEMPLATE_DIR.exists():
        TEMPLATE_DIR.mkdir(parents=True)

@template_bp.command(name='edit')
@click.argument('name')
def edit_template(name):
    """Create or Edit a template (.html or .md)."""

    # Better Prompt
    if '.' not in name:
        console.print(f"[dim]You didn't specify an extension for '{name}'.[/dim]")
        if click.confirm(f"Do you want to create, eidt or read'{name}.md'?"):
            name += '.md'
        else:
            console.print(f"[dim]Defaulting to '{name}.html'[/dim]")
            name += '.html'

    file_path = TEMPLATE_DIR / name

    # Boilerplate based on type
    if not file_path.exists():
        if name.endswith('.md'):
            # Note: We use Jinja {{ variables }} inside Markdown!
            content = "# Update for {{ name }}\n\nWrite your **formatted message** here.\n\n- Point 1\n- Point 2"
        else:
            content = "<h1>Hello {{ name }}</h1>\n<p>Write your update here.</p>"
        file_path.write_text(content)

    # Open Editor
    click.edit(filename=str(file_path))

    # Check if file was actually saved
    if file_path.exists():
        console.print(f"[green]✔ Template '{name}' saved.[/green]")
    else:
        console.print("[yellow]Edit cancelled (file not saved).[/yellow]")

@template_bp.command(name='delete')
@click.argument('name')
@click.confirmation_option(prompt='Are you sure?')
def delete_template(name):
    """Delete a template."""
    # Try to find the file even if user forgot extension
    file_path = TEMPLATE_DIR / name
    if not file_path.exists():
        # Try adding extensions
        if (TEMPLATE_DIR / f"{name}.md").exists():
            file_path = TEMPLATE_DIR / f"{name}.md"
        elif (TEMPLATE_DIR / f"{name}.html").exists():
            file_path = TEMPLATE_DIR / f"{name}.html"

    if file_path.exists():
        os.remove(file_path)
        console.print(f"[green]✔ Deleted {file_path.name}[/green]")
    else:
        console.print(f"[red]Template '{name}' not found.[/red]")

@template_bp.command(name='list')
@click.argument('query', required=False)
@click.option('--limit', default=10, help='Limit results')
@click.option('--offset', default=0, help='Pagination offset')
def list_templates(query, limit, offset):
    """List available templates (.html and .md)."""
    # 1. Fetch all valid files
    all_files = sorted(
        list(TEMPLATE_DIR.glob("*.html")) +
        list(TEMPLATE_DIR.glob("*.md"))
    )

    # 2. Filter (Search)
    if query:
        # Case-insensitive filename matching
        filtered_files = [f for f in all_files if query.lower() in f.name.lower()]
    else:
        filtered_files = all_files

    # 3. Paginate (Slice)
    # This mimics SQL "LIMIT ? OFFSET ?"
    start = offset
    end = offset + limit
    paged_files = filtered_files[start:end]

    # 4. Display Logic (The 3-State Feedback)
    if not paged_files:
        if query:
             # Scenario A: User searched, found nothing
            console.print(f"[yellow]No templates found matching '{query}'.[/yellow]")
        elif offset > 0 and filtered_files:
             # Scenario B: User paged too far
            console.print("[yellow]No more templates (end of list).[/yellow]")
        elif not all_files:
             # Scenario C: Folder is actually empty
            console.print("[yellow]No templates found. Create one with 'r-mail template edit <name>'[/yellow]")
        else:
            # Scenario D: Offset > 0 but no matches (edge case)
            console.print("[yellow]No more templates.[/yellow]")
        return

    table = Table(title=f"Email Templates {'(Filtered)' if query else ''}")
    table.add_column("Filename", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Size", style="green")

    for f in paged_files:
        ftype = "HTML" if f.suffix == '.html' else "Markdown"
        table.add_row(f.name, ftype, f"{f.stat().st_size} bytes")

    console.print(table)
