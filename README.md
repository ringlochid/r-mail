# r-mail 📧

**r-mail** is a developer-focused CLI email client designed for the VPS era. It replaces complex GUI mailers with a "Vim-First" workflow, supporting Markdown templates, encrypted credential storage, and cloud SMTP bypass (AWS SES).

## ✨ Features

* **Vim Integration:** Composes emails in your favorite editor (`$EDITOR`) automatically.
* **Markdown Support:** Writes in Markdown, sends as responsive HTML.
* **Smart Templates:** Jinja2 templates with YAML frontmatter for metadata and automatic variable prompting.
* **Context Profiles:** Database-backed profiles for managing recurring variables (Signatures, Links, Company Info).
* **Encrypted Vault:** SMTP passwords stored locally using Fernet encryption.
* **Cloud Ready:** Bypasses port 25/587 blocks(if you provider blocks these ports) using alternative ports (2587) for providers like AWS SES.
* **SQLite Backend:** Full CRUD management for Senders, Receivers, and Contexts with fuzzy search.

## 🛠️ Installation

The recommended way to install **r-mail** is using `pipx`. This creates an isolated environment for the tool while making the `r-mail` command available globally.

### Steps

1. **Install pipx** (if not already installed):
   ```bash
   # Debian / Ubuntu
   sudo apt update && sudo apt install -y pipx
   pipx ensurepath
   ```
   *(Restart your terminal after this step if it's your first time using pipx)*

2. **Clone & Install r-mail:**
   ```bash
   git clone https://github.com/ringlochid/r-mail.git
   cd r-mail

   # Install globally
   pipx install .
   ```

3. **Initialize the Database:**
   ```bash
   r-mail init
   ```

### 👨‍💻 For Developers
If you are modifying the code, install in "Editable Mode" so changes apply instantly:
```bash
pipx install -e . --force
```

## 🚀 Quick Start

### 1. Security Setup
Generate a master encryption key. This will be automatically appended to your shell configuration (e.g., `~/.bashrc`).

```bash
r-mail config setup-key
source ~/.bashrc
```

### 2. Configure a Domain (SMTP)
Add your SMTP provider.
* **Tip:** Use port **2587** if you are on a VPS (DigitalOcean/EC2) to bypass default firewall blocks.

```bash
r-mail domain add --name "aws" \
    --host "email-smtp.your-region-here.amazonaws.com" \
    --port 2587/587 \
    --user "YOUR_SMTP_USERNAME" \
    --security "STARTTLS"
```

### 3. Create an Identity
Link a "From" address (alias) to your configured domain.

```bash
r-mail sender add --alias "me" --name "myidentity" --email "me@example.com" --domain "smtpservice"
```

### 4. Send Your First Email
If you don't provide a body flag, **Vim** (or your default editor) will open automatically.

```bash
r-mail send -f me -t email@example.com -s "Hello World"
```

---

## 📝 Templates & Contexts

[Guide and example for creating smart templates](./GUIDE.md)

### Smart Templates (Markdown + Frontmatter)
Create templates that define their own required variables.

**Create:** `r-mail template edit newsletter.md`

```yaml
---
subject: Weekly Update
variables:
  headline: "Top Story Title"
  link: "Main URL"
---
# {{ headline }}

Check out our new update [here]({{ link }}).
```

**Send:**
```bash
r-mail send -f me -t client -p newsletter
```
*(The CLI will detect missing variables and interactively prompt you for `headline` and `link`.)*

### Context Profiles (Database Variables)
Manage recurring data sets (like signatures or project info) in the database.

**Create:** `r-mail context add work --template newsletter.md`

*(Vim opens JSON editor)*
```json
{
    "footer": "Sent from $(hostname)",
    "company": "Example inc"
}
```

**Apply:**
```bash
r-mail send -f me -t client -p newsletter -C work
```

---

## 📚 Command Reference

### Senders & Receivers
Manage your identity and address book.

```bash
# List senders (supports fuzzy search)
r-mail sender list [query]

# Add a recipient
r-mail receiver add --alias "bob" --email "bob@example.com"
```

### Domains
Manage SMTP server configurations.

```bash
r-mail domain list
r-mail domain delete <name>
```

### Contexts
Manage reusable variable profiles.

```bash
r-mail context list
r-mail context add <name> --description "My Context"
r-mail context update <name> --template <filename>
r-mail context edit <name>  # Opens Vim to edit JSON data
```

## 🐛 Local Debugging

You can start a local fake SMTP server to test email rendering without actually sending anything.

**1. Start the Server:**
```bash
python3 -m aiosmtpd -n -l localhost:1025
```

**2. Configure r-mail to use it:**
```bash
r-mail domain add --name "local" --host "localhost" --port 1025 --user "test" --security "NONE"
r-mail sender add --alias "debug" --email "test@localhost" --domain "local"
```
