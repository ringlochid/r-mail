import smtplib
import ssl
import os
import markdown
import frontmatter
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from rmail import database
from rmail.vault import Vault

def get_password(domain_name, username):
    """Fetch SMTP password from the encrypted Vault."""
    vault = Vault()
    return vault.get_password("rmail", domain_name)

def create_message(sender_email, receiver_email, subject, html_content, attachments=None):
    """Builds a multipart MIME message (HTML + Plaintext fallback + Attachments)."""
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # 1. Create the Body (Alternative: Text or HTML)
    msg_body = MIMEMultipart("alternative")

    # Generate Plain Text from HTML for better deliverability
    soup = BeautifulSoup(html_content, "html.parser")
    text_content = soup.get_text(separator="\n").strip()

    part_text = MIMEText(text_content, "plain")
    part_html = MIMEText(html_content, "html")

    msg_body.attach(part_text)
    msg_body.attach(part_html)
    msg.attach(msg_body)

    # 2. Process Attachments
    if attachments:
        for filepath in attachments:
            filename = os.path.basename(filepath)
            with open(filepath, "rb") as f:
                part = MIMEApplication(f.read(), Name=filename)
            part['Content-Disposition'] = f'attachment; filename="{filename}"'
            msg.attach(part)

    return msg

def send_email(sender_row, receiver_email, subject, html_body, attachments=None):
    """
    Orchestrates the sending process.
    sender_row: Dictionary containing domain and sender info from DB.
    """
    domain = sender_row['domain_name']
    host = sender_row['smtp_host']
    port = sender_row['smtp_port']
    user = sender_row['smtp_user']
    security = sender_row['security']

    # 1. Build the email
    msg = create_message(sender_row['email'], receiver_email, subject, html_body, attachments)

    # 2. Connect to SMTP
    try:
        print(f"Connecting to {host}:{port} ({security})...")
        server = smtplib.SMTP(host, port)

        if security == 'STARTTLS':
            server.starttls(context=ssl.create_default_context())
        elif security == 'SSL':
            server = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context())

        # 3. Login (Skip if NONE)
        if security != 'NONE':
            password = get_password(domain, user)
            if not password:
                raise ValueError(f"No password found in Vault for domain '{domain}' user '{user}'")
            server.login(user, password)

        # 4. Send
        server.send_message(msg)
        server.quit()
        return True

    except Exception as e:
        print(f"SMTP Error: {e}")
        raise e

def get_template_meta(template_name):
    """
    Returns: (metadata_dict, content_string, extension_found)
    """
    template_dir = database.APP_DIR / "templates"

    # Try finding the file and detecting extension
    file_path = None
    extension = ".html" # Default

    if (template_dir / template_name).exists():
        file_path = template_dir / template_name
        extension = file_path.suffix
    elif (template_dir / f"{template_name}.md").exists():
        file_path = template_dir / f"{template_name}.md"
        extension = ".md"
    elif (template_dir / f"{template_name}.html").exists():
        file_path = template_dir / f"{template_name}.html"
        extension = ".html"

    if not file_path:
        raise ValueError(f"Template '{template_name}' not found.")

    post = frontmatter.load(str(file_path))
    return post.metadata, post.content, extension

def render_template_content(content, extension, context={}):
    """
    Renders the raw content string (stripped of frontmatter).
    """
    # 1. Jinja2 Render
    env = Environment()
    template = env.from_string(content)
    rendered = template.render(**context)

    # 2. Markdown Render (if applicable)
    if extension == '.md':
        return markdown.markdown(rendered)
    return rendered

