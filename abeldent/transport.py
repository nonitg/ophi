"""One SQL round trip to the ABELDent lab VM through `lab/vm/vm sql`, which owns the read-only rails."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


class VmSqlError(RuntimeError):
    """The VM or the database rejected a query: unreachable VM, refused write, bad SQL."""


def _vm_error(text):
    """The database's own message, not PowerShell's wrapper around it."""
    text = text.strip()
    m = re.search(r'argument\(s\): "(.+?)"\s*$', text, re.M)  # SqlException via DataAdapter.Fill
    return m.group(1) if m else (text.splitlines()[0][:400] if text else "empty response from vm sql")


def sql(query, params=None, vm=None, mode="read"):
    """Run one query against the ABELDent database and return the last result set's rows as dicts.
    `@name` placeholders bind from `params`, so values never enter the SQL text.
    vm: path to colombus's lab/vm/vm (default: $ABELDENT_VM).
    mode: read (default), write (lab test data only) or dry-run (write, then roll back)."""
    vm = vm or os.environ.get("ABELDENT_VM")
    if not vm or not Path(vm).exists():
        raise VmSqlError(f"VM bridge not found at {vm!r}: pass vm= or set ABELDENT_VM to colombus/lab/vm/vm")
    args = [str(vm), "sql", query, "", "json", json.dumps(params or {}), mode]
    r = subprocess.run(args, capture_output=True, text=True)
    body = r.stdout.strip()
    # utm transport folds guest errors into stdout with exit 0; ssh reports them on stderr + exit code
    if r.returncode or not body or body.startswith("REFUSED") or "Exception" in body[:200]:
        raise VmSqlError(_vm_error(r.stderr if r.returncode and r.stderr.strip() else body))
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise VmSqlError(f"non-JSON from vm sql: {body[:300]}")
    if isinstance(data, dict):  # older q.ps1 shapes: {value,Count} wrapper or a bare single row
        data = data["value"] if "value" in data and "Count" in data else [data]
    return data
