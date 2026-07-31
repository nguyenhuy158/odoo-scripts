"""Audit the filestore: referenced vs missing vs orphan files, with sizes.

Read-only. Compares ir_attachment.store_fname against files on disk.
Attachments stored externally (matching EXTERNAL_STORE_PREFIXES, e.g.
s3:// or azure://) are counted separately and excluded from the local
disk cross-check.

Usage:
    click-odoo -c odoo.conf -d mydb scripts/filestore_audit.py
"""

import os
from collections import Counter

# Thay bằng prefix thực tế đang dùng.
# Ví dụ: ('s3://',) hoặc ('azure://', 's3://')
EXTERNAL_STORE_PREFIXES = ("PREFIX_EXTERNAL/",)

WIDTH = 62


def is_external_path(store_fname):
    return store_fname.startswith(EXTERNAL_STORE_PREFIXES)


def fmt_size(num_bytes):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if num_bytes < 1024 or unit == "TiB":
            return f"{num_bytes:.2f} {unit}" if unit != "B" else f"{num_bytes} B"
        num_bytes /= 1024


def bar(part, total, width=30):
    filled = int(round(width * part / total)) if total else 0
    pct = 100 * part / total if total else 0
    return f"[{'#' * filled}{'.' * (width - filled)}] {pct:5.1f}%"


def box_top(title):
    print(f"╔{'═' * WIDTH}╗")
    print(f"║{title.center(WIDTH)}║")
    print(f"╚{'═' * WIDTH}╝")


def section(title):
    print()
    print(f"┌─ {title} {'─' * (WIDTH - len(title) - 4)}")


def row(label, value):
    print(f"│ {label:<32} {value:>{WIDTH - 36}}")


Attachment = env["ir.attachment"].sudo()
filestore = Attachment._filestore()

env.cr.execute(
    """
    SELECT count(*), count(DISTINCT store_fname)
    FROM ir_attachment
    WHERE store_fname IS NOT NULL
    """
)
attachment_records, referenced_paths_count = env.cr.fetchone()

env.cr.execute(
    """
    SELECT DISTINCT store_fname
    FROM ir_attachment
    WHERE store_fname IS NOT NULL
    """
)
referenced_paths = {r[0] for r in env.cr.fetchall()}

external_paths = {path for path in referenced_paths if is_external_path(path)}
local_referenced_paths = referenced_paths - external_paths

disk_files = {}
for root, _, filenames in os.walk(filestore):
    for filename in filenames:
        path = os.path.join(root, filename)
        relative_path = os.path.relpath(path, filestore)

        if relative_path.startswith("checklist/"):
            continue

        disk_files[relative_path] = os.path.getsize(path)

existing_paths = local_referenced_paths & disk_files.keys()
missing_paths = local_referenced_paths - disk_files.keys()
orphan_paths = disk_files.keys() - local_referenced_paths

external_prefix_counts = Counter(
    next(prefix for prefix in EXTERNAL_STORE_PREFIXES if path.startswith(prefix))
    for path in external_paths
)

referenced_size = sum(disk_files[p] for p in existing_paths)
orphan_size = sum(disk_files[p] for p in orphan_paths)
total_size = sum(disk_files.values())

box_top(f"FILESTORE AUDIT — {env.cr.dbname}")
print(f"  {filestore}")

section("Database")
row("ir.attachment records", f"{attachment_records:,}")
row("Referenced physical files", f"{referenced_paths_count:,}")
row("Local referenced files", f"{len(local_referenced_paths):,}")

section("External storage")
row("External stored files", f"{len(external_paths):,}")
for prefix, count in sorted(external_prefix_counts.items()):
    row(f"  {prefix!r}", f"{count:,}")
if not external_paths:
    print(f"│ (none matching {EXTERNAL_STORE_PREFIXES})")

section("Local disk")
row("Files on disk", f"{len(disk_files):,}")
row("Total physical size", fmt_size(total_size))

section("Cross-check (local only)")
row("Referenced & existing", f"{len(existing_paths):,}")
row("Missing (in DB, not on disk)", f"{len(missing_paths):,}")
row("Orphan (on disk, not in DB)", f"{len(orphan_paths):,}")

section("Size breakdown")
print(f"│ referenced {bar(referenced_size, total_size)}  {fmt_size(referenced_size)}")
print(f"│ orphan     {bar(orphan_size, total_size)}  {fmt_size(orphan_size)}")

print()
if missing_paths:
    print(f"⚠  {len(missing_paths):,} attachment(s) point to local files that no longer exist!")
if orphan_paths:
    print(f"♻  {fmt_size(orphan_size)} reclaimable from orphan files.")
if not missing_paths and not orphan_paths:
    print("✔  Filestore is clean: no missing and no orphan local files.")
