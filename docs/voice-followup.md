# Should a voice agent phone patients on the Past denials list?

*A decision memo, written 2026-09-27, for the call list at `/recover`. The short answer: draft the script
with a model, let a person make the call. Do not build autonomous dialing.*

*Built 2026-09-27, later the same day: option 1, verifier first. See section 6.*

**In one sentence:** the regulatory line in Canada runs between "we are telling you something about your file"
and "we are selling you a crown", an AI voice sits on the wrong side of that line the moment it tries to book,
and the part of the job that is actually slow — knowing what to say — needs no telephony at all.

---

## 1. What the list is, and where the time actually goes

Each row at `/recover` is a patient whose crown preauthorization Sun Life denied and the clinic never resent.
The blocker is nearly always a document that needs the patient in the chair: a dated periapical radiograph, or
a six-point periodontal chart. The staffer's job is to call, explain, and get them booked.

Three things about that job shape this decision:

- **The list is finite.** It is pre-Ophi backfill. A denial that happens after go-live stays on the board in
  the `RESUBMIT` column (`ophi/workflow.py:37`), so this list drains and never refills. It is 10 rows today.
  Automation that takes weeks to build pays back against a list that is emptying.
- **Ophi cannot book.** The PMS binding is read-only and says so in the first line of
  `ophi/web/abeldent_api.py`. Even a perfect voice agent could not write the appointment; a human would still
  have to. That caps the ceiling of every autonomous design.
- **Dialing is not the bottleneck.** Knowing what to say is. The staffer calling Leila Farahani did not handle
  her denial eight months ago and has to reconstruct, from "Denied as per the plan criteria", why a crown she
  was promised never happened. That is the expensive part, and it is not a telephony problem.

## 2. The regulatory position

**This needs a lawyer before anything dials. I am not one.** But the shape of the constraint is clear enough to
design around, and it is the reason for the recommendation.

CRTC's Unsolicited Telecommunications Rules define an automatic dialing-announcing device (ADAD) as equipment
that conveys a "pre-recorded **or synthesized** voice message". An LLM voice agent is a synthesized voice placed
by automatic dialing equipment, so it is an ADAD. "Synthesized" predates good TTS by decades, and CRTC opened
consultation 2026-132 in June 2026 asking explicitly whether AI voice counts as a robocall — so the safe
assumption today is yes.

That splits into two branches:

| | The call is **solicitation** | The call is **administrative** |
|---|---|---|
| What it sounds like | "Your crown is still possible — we can get this covered, would Tuesday work?" | "There is an unfinished item on your file. Please call us back." |
| Consent needed | **Express prior consent** to receive automated calls | None |
| Does the existing-business-relationship exemption save you? | **No.** EBR exempts you from the Do Not Call List, not from the ADAD express-consent rule. | n/a |
| Other duties | — | Identification message (clinic, purpose, address + phone), calling hours, CLID, no sequential dialing |

Almost no dental patient has given express consent to receive a synthesized-voice call. Penalties run to
CAD 15,000 per violation for a corporation.

**The knife-edge is the whole problem.** The administrative branch is defensible only while the script stays
genuinely informational. The moment it names a benefit or asks for a booking, it is solicitation without
consent. Every product instinct will push the script toward booking, because that is where the money is. A
design whose compliance depends on nobody ever improving the script is not a safe design.

### One piece of luck

Ophi's copy law already bans the words that would make a script commercially persuasive:

```python
FORBIDDEN = re.compile(r"\b(will be approved|approved|eligible|covered|likely|probability)\b", re.I)
```
*(`tests/test_web.py:19`, enforced across every screen by `test_copy_law_in_ophi_voice`.)*

A script that passes the existing copy law is, very nearly by construction, non-solicitation. That is a rule we
already enforce, already test, and already agree with. **Reuse it rather than inventing a second rulebook.**

## 3. Options, ranked

| # | Option | Verdict |
|---|---|---|
| **1** | **Model drafts the script, a person calls** | **Do this.** No ADAD, no telephony vendor, no recording, no new processor of patient data beyond the model already in `ophi/letters.py`. Fixes the actual bottleneck. |
| 2 | Machine leaves voicemail, never converses | Buildable. Real compliance cost against a list of tens of patients that is shrinking. Revisit only if #1 shows the list gets worked and dialing is what's left. |
| 3 | Live conversation, callback time only | No. "When can you come in" is the sentence that flips the branch. |
| 4 | Autonomous booking | **No.** Needs consent we do not have, and we cannot write to the PMS anyway. |

If option 2 is ever built, the agent must hang up or transfer when a human answers — an agent that converses is
option 3 wearing a disguise.

## 4. How option 1 would be built

Two modules, mirroring patterns the repo already has.

**`ophi/callscript.py`** — copies the shape of `ophi/letters.py` exactly: a module-level `SYSTEM` prompt, a
pydantic output model, a `Drafter` callable seam so tests inject a fake, and a `CallScriptError` whose message is
fit to show staff. Same degradation contract as `letters.py:38-39`: if the model is unreachable, the page shows a
static fallback script and the staffer still works the list. Never a 500 at a busy front desk.

**`ophi/verify/callscript.py`** — an independent checker sharing no code with the drafter, the way the packet
verifier reopens every file with no shared code. This is where the safety actually lives. A draft reaches the
screen only if it passes:

1. **Copy law** — run `FORBIDDEN` over the text and reject, don't soften. This means promoting that regex out of
   `tests/test_web.py` into a module both the test and the verifier import. Worth doing anyway:
   `tests/test_pack_auto.py:31` already does `from tests.test_web import FORBIDDEN`, which is a smell.
2. **Grounding** — the tooth must equal `row.tooth_fdi`, the gaps named must be a subset of `row.gaps`, any
   dollar figure must equal `row.fee_dollars`. Reject invented facts rather than trusting the model.
3. **Payer voice** — Sun Life's words stay verbatim and attributed, inside `data-voice="payer"`, so
   `test_copy_law_in_ophi_voice` keeps passing on `/recover`. The script never paraphrases the payer.
4. **Voicemail minimization** — checked by *absence*, derived from the row so it cannot drift: no
   `row.tooth_fdi`, no gap token, no "Sun Life", no `\$\d`.

No new `FollowUpStatus`. A person still records the outcome, exactly as now.

## 5. Patient information

The clinic is a health information custodian under PHIPA; a model vendor and a telephony vendor both become its
agents, and the clinic stays liable. Practical rules:

- **Send the model initials, not a name.** `LookBackRow.patient_label` already exists (`ophi/lookback.py:29`)
  for exactly this. Template the real first name in locally after the draft returns, so the vendor never sees a
  named patient. Never send date of birth, patient id, phone, or any other row.
- **Do not add a phone number to `LookBackRow`.** It would be serialized into `followups.json` and handed to a
  model. `abeldent.Patient` already carries `phone`/`mobile` (`ophi/sources/abeldent.py:29-30`); fetch at dial
  time only, if there is ever a dial.
- **A voicemail's ceiling** is clinic name, patient first name, callback number. No tooth, no procedure, no
  insurer, no amount, no "denied". "Sun Life denied your crown" on a shared answering machine is a reportable
  breach, and someone other than the patient hears a good share of voicemails.
- **Audit the event, not the text.** Row id, actor, timestamp — the shape every other state change already uses.
  Never the script, never a number. Scripts are ephemeral: render and discard, nothing persisted to `var/`.
- **No recording of patient audio.** One-party consent makes it lawful and professional guidance still makes it
  a bad idea. If a vendor records by default, turn it off explicitly and verify it is off.
- **Separately worth fixing:** `ophi/letters.py` runs against a Gemini tier whose terms permit training on
  input. That is already questionable for letters carrying patient identity, independent of this feature.

## 6. The cheapest way to find out if this works

**Build the verifier first, before any drafter and before any UI.** Write `tests/test_callscript_verify.py` with
five good scripts and a dozen deliberately bad ones: says "covered"; names a tooth that is not on the row;
invents a gap; puts "Sun Life denied" in a voicemail; quotes a dollar figure; paraphrases the payer.

**If the verifier cannot reject all twelve, stop.** There is no version of this worth shipping where a machine
talks to a patient and nothing reliably catches it lying. That gate costs about a day and it is the whole
experiment.

Only then: the drafter behind a fake `Drafter` in tests, then an `evals/` harness running the real model over
the `cases/lookback/` fixtures — synthetic patients only — reporting the verifier's rejection rate. **If more
than roughly 1 draft in 20 is rejected, fall back to a static template with slots.** That would be cheaper, fully
predictable, and probably good enough, since the staffer only needs the facts assembled, not prose.

None of this places a call or touches a real patient.

---

## Open before anything dials

- A lawyer on the solicitation/ADAD question, specifically whether a "there is an item on your file" script
  survives contact with a regulator.
- PHIPA agent agreements with the model vendor, and the telephony vendor if option 2 ever ships.
- Whether the Gemini tier behind `letters.py` trains on input — a live question today, not just for this.

## Sources

[CRTC Unsolicited Telecommunications Rules](https://www.crtc.gc.ca/eng/trules-reglest.htm) ·
[Key rules for telemarketers](https://crtc.gc.ca/eng/phone/telemarketing/tobligations/rules-regles.htm) ·
[CRTC 2014-155](https://crtc.gc.ca/eng/archive/2014/2014-155.htm) ·
[CRTC 2026-132](https://crtc.gc.ca/eng/archive/2026/2026-132.htm) ·
[IPC Ontario PHIPA FAQ](https://www.ipc.on.ca/sites/default/files/legacy/2015/11/phipa-faq.pdf)

---

## 6. What was built, 2026-09-27

Option 1, in the order section 4 prescribed: the verifier first, against a corpus of thirteen deliberately bad
scripts, and the drafter only once every one of them was rejected for the right reason
(`tests/test_callscript.py`).

- **`ophi/verify/callscript.py`** — `verify_script(text, row, clinic)`. Ten checks: the copy law, an explicit
  no-promise rule, tooth grounding against `row.tooth_fdi`, no fee quoted at all, date grounding against
  `row.submitted_on`, gap grounding against `row.gaps`, no invented name, the clinic identified, a word cap,
  and non-empty. Shares no code with the drafter.
- **`ophi/callscript.py`** — `draft_call_script(row, clinic)`. Gemini via the `ophi/letters.py` client, given
  `facts(row, clinic)`: initials, tooth, submission date, Sun Life's words, and the gaps. It re-asks once with
  the verifier's findings, and **raises rather than returning an unverified draft** — no draft at all beats one
  a staffer reads out and has to walk back. Staff still write their own notes.
- **`POST /recover/{row_id}/script`** — drafts on demand, renders beside the row, never on page load.

Two deviations from section 4, both deliberate:

1. **The copy law moved, rather than being copied.** `FORBIDDEN` now lives in `ophi/copy_law.py`;
   `tests/test_web.py` re-exports it so `tests/test_pack_auto.py` keeps working, and the verifier imports it.
   Section 4 called for this and it is what keeps the compliance argument honest: one rulebook, enforced in the
   same words the screens are held to. `SPOKEN_EXTRA` adds *approval*, *coverage* and *guarantee* — the words a
   model reaches for on the phone and never on a screen.
2. **Voicemail minimization is not implemented.** It is a check by absence for a call Ophi does not place.
   Build it with the voicemail, if there is ever one.

Still true, and still the reason not to go further: nothing dials, and the PMS stays read-only.