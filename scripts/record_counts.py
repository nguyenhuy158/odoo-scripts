"""Count records of common models — quick database overview.

Usage:
    click-odoo -c odoo.conf -d mydb scripts/record_counts.py
"""

MODELS = [
    "res.partner",
    "res.users",
    "sale.order",
    "purchase.order",
    "account.move",
    "stock.picking",
    "ir.attachment",
]

print(f"{'model':<20} count")
print("-" * 30)
for model in MODELS:
    if model not in env:
        print(f"{model:<20} (not installed)")
        continue
    count = env[model].sudo().search_count([])
    print(f"{model:<20} {count}")
