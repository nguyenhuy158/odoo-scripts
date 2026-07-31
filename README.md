# odoo-scripts

Collection of scripts runnable with [click-odoo](https://github.com/acsone/click-odoo).

Each script is a plain Python file. `click-odoo` injects an initialized Odoo
environment as the global variable `env` (the `odoo` module is also available),
so scripts don't need any boilerplate.

## Requirements

Install in the **same virtualenv as Odoo**:

```bash
pip install click-odoo
```

## Usage

```bash
click-odoo -c /etc/odoo/odoo.conf -d mydb scripts/list_users.py
```

Common flags:

| Flag | Description |
| --- | --- |
| `-c <file>` | Odoo config file |
| `-d <db>` | Database name |
| `--rollback` | Dry run — roll back the transaction at the end |
| `--log-level warn` | Quieter output |

The transaction is committed automatically when the script finishes without
error, and rolled back on exception.

Run without a script file to get an interactive REPL with `env` available:

```bash
click-odoo -c /etc/odoo/odoo.conf -d mydb
```

## Scripts

| Script | Description | Safe (read-only) |
| --- | --- | --- |
| `scripts/list_users.py` | List active users with login and email | ✅ |
| `scripts/record_counts.py` | Count records of common models | ✅ |
| `scripts/deactivate_user.py` | Deactivate a user by login (edit LOGIN first) | ❌ writes |
| `scripts/filestore_audit.py` | Audit filestore: referenced vs missing vs orphan files, sizes | ✅ |
| `scripts/attachment_by_model.py` | Attachment disk usage grouped by res_model, biggest first | ✅ |

## Writing a new script

1. Create a file under `scripts/`.
2. Use the `env` global directly — no imports needed.
3. Test with `--rollback` first:

```bash
click-odoo -c /etc/odoo/odoo.conf -d mydb --rollback scripts/my_script.py
```

Template:

```python
"""One-line description of what the script does."""

records = env["res.partner"].search([("customer_rank", ">", 0)], limit=10)
for r in records:
    print(r.name)
```
