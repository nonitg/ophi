How a PMS works — the mental model

A dental PMS is four systems that share a patient ID and pretend to be one app. Learn the four and ABELDent stops being mysterious.

1. The schedule. Chairs × time. Appointments carry a patient, a provider, a duration, and a planned procedure. This drives the front desk, not the clinical record.

2. The chart (clinical). Three separate stores that people lump together:
- Odontogram — per-tooth, per-surface state. Tooth #46, mesial-occlusal, existing amalgam. Teeth are numbered; Canada uses FDI (11–48) but US notation (1–32) leaks in through US-built modules. Notation mismatch is a top-5 source of silent wrong answers, which is why your plan names it explicitly in the evidence matcher.
- Perio chart — 6 measurements per tooth (pocket depth at 6 sites), plus recession, bleeding, furcation, mobility. 32 teeth × 6 = 192 points for a full-mouth exam. "Point count" in your M0 exit criterion means exactly this: did the hygienist record 192 points or 12? A CDCP crown rule that wants perio evidence needs to know the difference between a full exam and a spot check.
- Clinical notes — free text, sometimes templated. This is where the justification for a crown actually lives, in prose, unstructured.

3. The ledger. Every procedure has two lives: planned (treatment plan, not done, no money) and completed (done, billable, dated). Same procedure code, different table or different status flag. Getting this wrong is the classic integration bug — you report a crown as completed when it's only proposed. ABELDent calls these the Treatment Ledger and the Financial Ledger, and Sikka's docs confirm it distinguishes Provider from Responsible Provider, which is a second trap: who did it vs. who owns the patient.

4. Insurance. A patient has one or more coverages (carrier, policy, group, certificate, relationship to subscriber). A claim says "this was done, pay me." A predetermination (= preauthorization) says "I intend to do this, will you pay?" — same message format, different transaction code, no money moves. That's your entire product surface: the predetermination path.

Why preauth is painful, concretely. The procedure code (27xxx = crown) is structured. The tooth is structured. But the evidence CDCP wants — a periapical radiograph from within 12 months, a perio chart, a note explaining why a filling won't hold — lives in three different subsystems, in three different formats, one of which is prose and one of which is a JPEG owned by a separate imaging vendor. A human opens four screens and eyeballs dates. That manual cross-subsystem join is what Colombus automates.

And the thing your plan already knows: four of the CDCP crown criteria (crown-to-root ratio, furcation, margin-to-crest distance, ferrule height) are not fields in any PMS. They're measurements a dentist makes by looking at the film. No amount of database reading produces them. Hence the Clinician Assertions block.