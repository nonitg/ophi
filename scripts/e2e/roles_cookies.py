"""Roles lane: actor-cookie handling and malformed form input. Nothing here is meant to mutate."""
import re
import httpx

BASE = "http://127.0.0.1:8765"

def flat(html):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def acting_as(cookies):
    """Who the app says it is acting as, read off the worklist's View-as control."""
    r = httpx.get(f"{BASE}/", cookies=cookies, timeout=60)
    sel = re.search(r'<select[^>]*name="actor".*?</select>', r.text, re.S)
    chosen = re.findall(r'<option[^>]*selected[^>]*>(.*?)</option>', sel.group(0)) if sel else []
    return r.status_code, (chosen[0].strip() if chosen else "?")

print("== A. actor cookie fallback ==")
for label, val in [("absent", None), ("junk", "wharrgarbl"), ("empty", ""),
                   ("Dentist", "Dentist"), ("DENTIST", "DENTIST"), ("dentist ", "dentist "),
                   ("path-ish", "../../etc/passwd"), ("xss", "<script>alert(1)</script>")]:
    ck = {} if val is None else {"actor": val}
    try:
        print(f"  {label:12} -> {acting_as(ck)}")
    except Exception as e:
        print(f"  {label:12} -> EXC {e!r}")

print("== B. cookie attributes set by POST /actor ==")
for val in ("dentist", "coordinator", "junkvalue"):
    r = httpx.post(f"{BASE}/actor", data={"actor": val}, timeout=60, follow_redirects=False)
    print(f"  actor={val!r} {r.status_code} set-cookie={r.headers.get('set-cookie')!r}")
r = httpx.post(f"{BASE}/actor", data={}, timeout=60, follow_redirects=False)
print(f"  actor missing -> {r.status_code} {flat(r.text)[:140]}")

print("== C. /rules/use with odd actor cookies (dentist-only + 'who is this') ==")
for val in (None, "junk", "Dentist", "coordinator", "dentist"):
    ck = {} if val is None else {"actor": val}
    r = httpx.post(f"{BASE}/rules/use", data={"draft": "x", "draft_sha": "y"}, cookies=ck, timeout=60, follow_redirects=False)
    print(f"  actor={val!r} -> {r.status_code} {flat(r.text)[:110]}")

print("== D. missing required Form fields ==")
MISSING = [("assert", "/cases/abeldent_166/assert", {}),
           ("proposals", "/cases/abeldent_166/proposals/art_x", {}),
           ("recover", "/recover/lb03", {}),
           ("letter", "/cases/abeldent_164/letter", {})]
for name, path, data in MISSING:
    r = httpx.post(BASE + path, data=data, cookies={"actor": "dentist"}, timeout=60, follow_redirects=False)
    print(f"  {name:10} {r.status_code} ct={r.headers.get('content-type','')[:30]} {flat(r.text)[:110]}")

print("== E. absurd values ==")
LONG = "The patient reports pain. " * 400  # ~10k chars
ABSURD = [
  ("decision outcome not in set", "/cases/abeldent_164/decision", {"outcome": "maybe", "decided_on": "2026-09-01"}),
  ("decision date 1899",          "/cases/abeldent_164/decision", {"outcome": "approved", "decided_on": "1899-01-01"}),
  ("decision date 2999",          "/cases/abeldent_164/decision", {"outcome": "approved", "decided_on": "2999-01-01"}),
  ("decision date garbage",       "/cases/abeldent_164/decision", {"outcome": "approved", "decided_on": "not-a-date"}),
  ("decision bogus reason_key",   "/cases/abeldent_164/decision", {"outcome": "denied", "decided_on": "2026-09-01", "reason_key": "zzz"}),
  ("booked date 2999",            "/cases/abeldent_166/booked",   {"on": "2999-01-01"}),
  ("booked date garbage",         "/cases/abeldent_166/booked",   {"on": "31/12/2026"}),
  ("submitted date 2999",         "/cases/abeldent_164/submitted",{"on": "2999-01-01"}),
  ("narrative 10k ungrounded",    "/cases/abeldent_164/narrative",{"narrative": LONG}),
  ("recover bad status",          "/recover/lb03",                {"status": "teleported", "note": "roles-lane probe"}),
  ("recover 10k note",            "/recover/lb03",                {"status": "teleported", "note": LONG}),
  ("undo bogus step",             "/cases/abeldent_166/undo",     {"step": "../../etc"}),
  ("assert value out of set",     "/cases/abeldent_166/assert",   {"criterion_id": "x", "value": "\u0000" * 50}),
  ("case id traversal",           "/cases/..%2F..%2Fetc/undo",    {"step": "sent"}),
  ("case id 5k",                  "/cases/" + "a" * 5000 + "/undo", {"step": "sent"}),
]
for name, path, data in ABSURD:
    try:
        r = httpx.post(BASE + path, data=data, cookies={"actor": "dentist"}, timeout=60, follow_redirects=False)
        print(f"  {name:28} {r.status_code} {flat(r.text)[:120] if r.status_code>=400 else r.headers.get('location')}")
    except Exception as e:
        print(f"  {name:28} EXC {e!r}")

print("== F. double submit (same payload twice) ==")
for name, path, data in [("submitted x2", "/cases/abeldent_164/submitted", {"on": ""}),
                         ("decision incomplete x2", "/cases/abeldent_164/decision", {"outcome": "", "decided_on": ""}),
                         ("rules/check x2", "/rules/check", {})]:
    out = []
    for _ in range(2):
        r = httpx.post(BASE + path, data=data, cookies={"actor": "coordinator"}, timeout=90, follow_redirects=False)
        out.append(f"{r.status_code}:{r.headers.get('location') or flat(r.text)[:50]}")
    print(f"  {name:24} {out}")
