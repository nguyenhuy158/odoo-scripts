"""Attachment disk usage grouped by res_model, biggest first.

Read-only. For each model: existing file count, missing file count,
total size on disk, and share of the grand total.

Usage:
    click-odoo -c odoo.conf -d mydb scripts/attachment_by_model.py
"""

import os
from collections import defaultdict

MODEL_W = 42
LINE_W = MODEL_W + 52


def fmt_size(num_bytes):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if num_bytes < 1024 or unit == "TiB":
            return f"{num_bytes:.2f} {unit}" if unit != "B" else f"{num_bytes} B"
        num_bytes /= 1024


def bar(part, total, width=16):
    filled = int(round(width * part / total)) if total else 0
    pct = 100 * part / total if total else 0
    return f"[{'#' * filled}{'.' * (width - filled)}] {pct:5.1f}%"


Attachment = env["ir.attachment"].sudo()
filestore = Attachment._filestore()

env.cr.execute(
    """
    SELECT
        COALESCE(res_model, '<no model>'),
        store_fname
    FROM ir_attachment
    WHERE store_fname IS NOT NULL
    """
)

model_paths = defaultdict(set)
for model, store_fname in env.cr.fetchall():
    model_paths[model].add(store_fname)

results = []
for model, paths in model_paths.items():
    total_bytes = 0
    existing_files = 0
    missing_files = 0

    for store_fname in paths:
        path = os.path.join(filestore, store_fname)
        if os.path.isfile(path):
            total_bytes += os.path.getsize(path)
            existing_files += 1
        else:
            missing_files += 1

    results.append((total_bytes, model, existing_files, missing_files))

grand_total = sum(size for size, _, _, _ in results)
total_missing = sum(missing for _, _, _, missing in results)

print(f"╔{'═' * LINE_W}╗")
print(f"║{('ATTACHMENTS BY MODEL — ' + env.cr.dbname).center(LINE_W)}║")
print(f"╚{'═' * LINE_W}╝")
print(f"  {filestore}")
print()

header = f"{'MODEL':<{MODEL_W}} {'FILES':>9} {'MISSING':>8} {'SIZE':>11}  SHARE"
print(header)
print("─" * LINE_W)

for size, model, files, missing in sorted(results, reverse=True):
    print(
        f"{model[:MODEL_W]:<{MODEL_W}} "
        f"{files:>9,} "
        f"{missing:>8,} "
        f"{fmt_size(size):>11}  "
        f"{bar(size, grand_total)}"
    )

print("─" * LINE_W)
print(
    f"{'TOTAL':<{MODEL_W}} "
    f"{sum(f for _, _, f, _ in results):>9,} "
    f"{total_missing:>8,} "
    f"{fmt_size(grand_total):>11}"
)

print()
if total_missing:
    print(f"⚠  {total_missing:,} referenced file(s) missing from disk.")
else:
    print("✔  No missing files.")
