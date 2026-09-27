"""Roles lane: confirm which actor the app falls back to for odd cookie values (aria-pressed)."""
import re, httpx
BASE = "http://127.0.0.1:8765"

def pressed(cookies):
    r = httpx.get(f"{BASE}/", cookies=cookies, timeout=60)
    on = re.findall(r'<button type="submit" name="actor" value="([a-z]+)" aria-pressed="true">'
                    r'<span class="mono-mark" aria-hidden="true">[^<]*</span>([^<]*)</button>', r.text)
    raw = "wharrgarbl" in r.text or "<script>alert(1)</script>" in r.text
    return r.status_code, on, ("COOKIE ECHOED IN HTML" if raw else "no echo")

for label, val in [("absent", None), ("junk", "wharrgarbl"), ("empty", ""), ("Dentist", "Dentist"),
                   ("DENTIST", "DENTIST"), ("trailing-space", "dentist%20"), ("dentist", "dentist"),
                   ("xss", "<script>alert(1)</script>"), ("very-long", "d" * 4000)]:
    ck = {} if val is None else {"actor": val}
    try:
        print(f"  {label:15} {pressed(ck)}")
    except Exception as e:
        print(f"  {label:15} EXC {e!r}")

print("== unknown case id on endpoints with no existence check ==")
for ep, data in [("undo", {"step": "sent"}), ("decision", {"outcome": "approved", "decided_on": "2026-09-01"}),
                 ("resubmit", {}), ("ask/done", {}), ("booked", {"on": "2026-10-01"}),
                 ("test-restore", {}), ("narrative", {"narrative": "x"})]:
    r = httpx.post(f"{BASE}/cases/no_such_case_xyz/{ep}", data=data, cookies={"actor": "coordinator"},
                   timeout=60, follow_redirects=False)
    t = re.sub(r"<[^>]+>", " ", r.text); t = re.sub(r"\s+", " ", t).strip()
    print(f"  {ep:12} {r.status_code} {t.split('—')[0][:60]!r}")

print("== decision with a bogus reason_key: what does the error page actually say ==")
r = httpx.post(f"{BASE}/cases/abeldent_164/decision",
               data={"outcome": "denied", "decided_on": "2026-09-01", "reason": "", "reason_key": "zzz"},
               cookies={"actor": "coordinator"}, timeout=60, follow_redirects=False)
m = re.search(r'<main.*?</main>', r.text, re.S)
t = re.sub(r"<[^>]+>", " ", m.group(0) if m else r.text); print("  ", r.status_code, re.sub(r"\s+", " ", t).strip()[:300])
