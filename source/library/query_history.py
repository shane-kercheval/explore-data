"""Persists a small per-source history of recently run SQL queries to local JSON files."""
import json
import os
import re
import tempfile
from contextlib import suppress
from datetime import datetime, timezone

HISTORY_DIR = '.query_history'
MAX_ENTRIES = 20
# The row itself truncates visually (CSS ellipsis) to fill whatever space is actually
# available; this is just a sane ceiling so a pathologically long query doesn't bloat the
# DOM/payload.
PREVIEW_MAX_LENGTH = 500


def _history_path(source: str) -> str:
    return os.path.join(HISTORY_DIR, f'{source}.json')


def _normalize_entries(raw: object) -> list[dict]:
    """
    Validate/coerce whatever was loaded from disk into a clean `list[dict]`.

    This is a local, user-editable cache file; valid-JSON-but-wrong-shape content (not a
    list, entries missing `sql`, etc.) is realistic, not just a hypothetical. Every other
    function in this module relies on entries always having a non-empty string `sql`, a
    `title` that's a string or `None`, and a string `last_used` - so that guarantee is
    enforced once, here, rather than trusted by (and duplicated across) every caller.
    Malformed entries are dropped rather than raised on, since losing one bad row is far
    better than the history (or, via the page-load refresh callback, the whole app)
    becoming permanently unusable until someone hand-fixes the JSON file.
    """
    if not isinstance(raw, list):
        return []
    entries = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        sql = entry.get('sql')
        if not isinstance(sql, str) or not sql.strip():
            continue
        title = entry.get('title')
        if not isinstance(title, str):
            title = None
        last_used = entry.get('last_used')
        if not isinstance(last_used, str):
            last_used = ''
        entries.append({'sql': sql, 'title': title, 'last_used': last_used})
    return entries


def load_history(source: str) -> list[dict]:
    """Load the history for a source (e.g. 'snowflake', 'bigquery'), most-recent first."""
    path = _history_path(source)
    if not os.path.isfile(path):
        return []
    try:
        with open(path) as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    entries = _normalize_entries(raw)
    entries.sort(key=lambda e: e['last_used'], reverse=True)
    return entries


def _save_history(source: str, entries: list[dict]) -> None:
    """
    Persist `entries`, replacing the file atomically.

    Writing directly to the target path with `open(path, 'w')` truncates it before the
    new content is fully written; anything that interrupts that window (a crash, the
    process getting killed) leaves an empty/corrupt file, which looks like the history
    silently vanished. Writing to a temp file first and swapping it in with `os.replace`
    (atomic on both POSIX and Windows) means the real file is always either the old
    complete version or the new complete version, never a partial one.
    """
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = _history_path(source)
    fd, tmp_path = tempfile.mkstemp(dir=HISTORY_DIR, prefix=f'.{source}.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(entries, f, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        with suppress(OSError):
            os.remove(tmp_path)
        raise


def record_query(source: str, sql: str) -> list[dict]:
    """
    Add/bump `sql` to the front of the history for `source` and persist it.

    If the (trimmed) query already exists, its title is preserved and it's moved to the
    front rather than being duplicated. Returns the updated, most-recent-first history.
    """
    sql = sql.strip() if sql else ''
    if not sql:
        return load_history(source)

    entries = load_history(source)
    existing = next((e for e in entries if e['sql'] == sql), None)
    entries = [e for e in entries if e['sql'] != sql]
    entries.insert(0, {
        'sql': sql,
        'title': existing.get('title') if existing else None,
        'last_used': datetime.now(timezone.utc).isoformat(),
    })
    entries = entries[:MAX_ENTRIES]
    _save_history(source, entries)
    return entries


def update_title(source: str, sql: str, title: str | None) -> list[dict]:
    """Set (or clear, if `title` is falsy) the user-friendly title for a cached query."""
    sql = sql.strip() if sql else ''
    entries = load_history(source)
    for entry in entries:
        if entry['sql'] == sql:
            entry['title'] = title or None
            break
    _save_history(source, entries)
    return entries


def delete_query(source: str, sql: str) -> list[dict]:
    """Remove a cached query for `source` (no-op if it's already gone)."""
    sql = sql.strip() if sql else ''
    entries = [e for e in load_history(source) if e['sql'] != sql]
    _save_history(source, entries)
    return entries


def truncate_sql_preview(sql: str, max_length: int = PREVIEW_MAX_LENGTH) -> str:
    """
    Collapse a SQL query onto a single line for display in a list row.

    Visual truncation to fit the row is handled by CSS (`text-overflow: ellipsis`);
    `max_length` is only a ceiling against pathologically long queries.
    """
    single_line = re.sub(r'\s+', ' ', sql).strip()
    if len(single_line) <= max_length:
        return single_line
    return single_line[:max_length].rstrip() + '…'
