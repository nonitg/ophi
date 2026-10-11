# abeldent

ABELDent read queries (`reads.py`) and the lab VM transport (`transport.py`), shared by colombus
and ophi-phone so both read the PMS with the same SQL.

**Reads only.** colombus never writes to a PMS. ophi-phone's writes (book on staff approval) live in
ophi-phone, never here.

- colombus imports it from the repo root, like `ophi` (root `pyproject.toml`; the demo deploy stages it).
- ophi-phone installs this directory on its own: `pip install -e ../colombus/abeldent`, or
  `abeldent @ git+https://github.com/nonitg/colombus@<commit>#subdirectory=abeldent`.
- `transport.sql` shells out to colombus's `lab/vm/vm sql`; pass `vm=` or set `ABELDENT_VM`.

A changed query changes what both repos see. Run both test suites, and note that colombus's recorded
snapshot (`mocks/pms/snapshot.json`) is keyed by query text.
