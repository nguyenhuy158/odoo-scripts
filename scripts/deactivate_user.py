"""Deactivate a user by login. EDIT LOGIN BELOW before running.

Writes data — test with --rollback first:
    click-odoo -c odoo.conf -d mydb --rollback scripts/deactivate_user.py
"""

LOGIN = "someone@example.com"  # <-- change me

user = env["res.users"].search([("login", "=", LOGIN)], limit=1)
if not user:
    raise SystemExit(f"user not found: {LOGIN}")

user.active = False
print(f"deactivated: {user.login} ({user.name})")
