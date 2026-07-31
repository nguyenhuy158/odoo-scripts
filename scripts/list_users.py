"""List active users with login, name, and email.

Usage:
    click-odoo -c odoo.conf -d mydb scripts/list_users.py
"""

users = env["res.users"].search([("active", "=", True)], order="login")

print(f"{'login':<30} {'name':<30} email")
print("-" * 90)
for user in users:
    print(f"{user.login:<30} {user.name:<30} {user.email or '-'}")

print(f"\n{len(users)} active users")
