# E2E run brief (shared by every E2E agent)

App under test: http://127.0.0.1:8765 — already running, live ABELDent VM data + live Laya/LightGBM on GPU.
Do not restart it, do not POST /reset, do not run `make reset` or `rm -rf var/` (var/models holds 1.6 GB of weights).

## How to drive it
- Python Playwright: `.venv/bin/python` (playwright 1.63, chromium installed). Headless.
- Put each script at `scripts/e2e/<lane>.py`; screenshots and JSON output under `var/e2e/<lane>/`.
- Page loads run the models live: use `timeout=30000` and `wait_until="load"`.
- Actor switch: set cookie `actor` = `dentist` or `coordinator` on the context, or POST form `actor=` to `/actor`.
  Actors come from `ophi/web/present.py`: the dentist signs in under the PMS's provider name (Dr. Terry Ackerman
  on the lab VM), coordinator = Kim Osei (default).
- Server log: `var/e2e-serve.log` — grep it for tracebacks after your lane runs.

## Rules
- You are testing, not fixing. Do NOT edit anything under `ophi/`, `lab/`, or `tests/`. Report defects instead.
- Stay inside the cases your prompt assigns you. Other agents mutate other cases at the same time.
- Every claim you report must come from something you observed: HTTP status, DOM text, screenshot, or log line.

## What counts as a finding
- HTTP 5xx, traceback in the log, JS console error, broken link, form post that does nothing.
- A control that a role should not have, or is missing for a role that needs it.
- Copy that misleads a clinic admin (wrong name, wrong date, wrong money, wrong next step).
- Layout: horizontal overflow at 1440x900 and at 390x844, unreadable overlap, clipped text.
- Dead weight: a screen or control an admin would never use.

## Report format (your final message, nothing else)
```
## <lane> — <n> findings
### F1 <one-line title>  [severity: high|med|low]
Where: <url / selector>
Saw: <observed>
Expected: <what a clinic admin needs>
Evidence: <screenshot path / log line / status>
```
Then a `## Worked` list of flows that passed, one line each.
