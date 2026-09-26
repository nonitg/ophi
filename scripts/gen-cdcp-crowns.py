"""Generate a realistic synthetic set of CDCP crown preauth decisions for the past-outcomes demo.

Each request starts from a hidden clinical state (tooth, restorations, endo, perio, pending work,
clinic habits). That state is rendered the way a clinic would submit it: dated attachments, a perio
summary, a treatment plan and a free-text note whose quality depends on the clinic. A simulated Sun
Life dental consultant then applies the CDCP Guide 6.3.5 criteria to what it can see, with noise.

Calibrated to public figures: crowns ~37% approved (Health Canada via Oral Health Group, May 2026);
roughly 30% of denials are incomplete submissions, the rest clinical, duplicate or ineligible; CDCP
members are mostly seniors. Sun Life letters are often vague, so ~35% of denials carry only
"does not meet CDCP criteria". Research notes: docs/research/cdcp-rules.md §3, §6, §7.

All people and IDs are fabricated. `_generator_truth` records what the generator knows and the
submission may not show; nothing that learns from this data may read it. Writes fixtures/cdcp_crowns/.
"""
import json
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "fixtures" / "cdcp_crowns"
N = 600
random.seed(2026)

CROWNS = [("27201", "Crown, porcelain/ceramic", 1210.0), ("27211", "Crown, porcelain/ceramic fused to metal", 1150.0),
          ("27301", "Crown, cast metal", 1120.0)]
SEXTANTS = {"S1": [18, 17, 16, 15, 14], "S2": [13, 12, 11, 21, 22, 23], "S3": [24, 25, 26, 27, 28],
            "S4": [34, 35, 36, 37, 38], "S5": [43, 42, 41, 31, 32, 33], "S6": [48, 47, 46, 45, 44]}
SEXTANT_OF = {t: s for s, teeth in SEXTANTS.items() for t in teeth}
MOLARS, PREMOLARS = [16, 17, 26, 27, 36, 37, 46, 47], [14, 15, 24, 25, 34, 35, 44, 45]
ANTERIORS, THIRD_MOLARS = [11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43], [18, 28, 38, 48]
AGE_BANDS = [("0-17", 0.03), ("18-64", 0.27), ("65-69", 0.22), ("70-74", 0.2), ("75-86", 0.22), ("87+", 0.06)]
COPAY = {"<70k": 0, "70k-80k": 40, "80k-90k": 60}

# Clinic habits drive most documentation gaps: a sloppy clinic is sloppy on every request.
N_CLINICS = 40
CLINICS = [{"id": f"SYN-P-{4000 + i}", "doc_care": random.betavariate(5, 2), "note_style": random.choice(["terse", "standard", "detailed"]),
            "channel": random.choices(["cdanet_eclaim", "provider_portal", "paper"], [0.45, 0.4, 0.15])[0],
            "specialty": random.choices(["general_dentist", "prosthodontist"], [0.9, 0.1])[0],
            "stale_fee_table": random.random() < 0.08} for i in range(N_CLINICS)]

# Consultant patterns, most decisive first. p = chance the consultant acts on it when it can see it.
# (code, category, CDCP Guide wording used on a specific letter, fixable-on-resubmission)
PATTERNS = {
    "age_under_18":      (0.97, "ELIGIBILITY", "eligibility", "Crowns are a benefit for clients 18 and older.", False),
    "third_molar":       (0.95, "TOOTH_INELIGIBLE", "coverage", "Third molars are eligible only where the first and second molars are missing and the third molar is in occlusion.", False),
    "duplicate":         (0.95, "DUPLICATE_REQUEST", "administrative", "Duplicate of a preauthorization already on file.", False),
    "frequency":         (0.92, "FREQ_LIMIT", "frequency", "Exceeds frequency: 1 crown per tooth per 96 months.", False),
    "no_pa":             (0.88, "DOC_MISSING_RADIOGRAPH", "incomplete_submission", "A current periapical radiograph of the requested tooth is required.", True),
    "stale_pa":          (0.75, "DOC_RADIOGRAPH_STALE", "incomplete_submission", "Radiographs must be dated within 12 months of the submission.", True),
    "no_perio":          (0.5, "DOC_MISSING_PERIO_CHART", "incomplete_submission", "A complete periodontal charting within 12 months is required for crowns.", True),
    "no_bw":             (0.35, "DOC_MISSING_RADIOGRAPH", "incomplete_submission", "Bitewing radiographs (right and left) within 12 months are required.", True),
    "pending_basic":     (0.8, "CLIN_ACTIVE_DISEASE", "clinical_necessity", "All basic treatment for active caries and periodontal disease must be completed before a crown is requested.", True),
    "endo_not_healed":   (0.72, "CLIN_ENDO_NOT_HEALED", "clinical_necessity", "An endodontically treated tooth must have healed before a crown is requested.", True),
    "not_ext_restored":  (0.82, "CLIN_NOT_EXT_RESTORED", "clinical_necessity", "The tooth does not meet the CDCP definition of extensively restored; a less costly restoration is indicated.", False),
    "crack_or_cosmetic": (0.85, "CLIN_NOT_COVERED_INDICATION", "clinical_necessity", "Crowns for cracked tooth syndrome, sensitivity or aesthetics are not covered.", False),
    "active_perio":      (0.7, "CLIN_PERIO_PROGNOSIS", "clinical_necessity", "Active periodontal disease at the requested tooth.", True),
    "poor_support":      (0.85, "CLIN_PERIO_PROGNOSIS", "clinical_necessity", "Crown-to-root ratio or bone support does not meet CDCP criteria.", False),
    "furcation":         (0.85, "CLIN_PERIO_PROGNOSIS", "clinical_necessity", "Furcation involvement at the requested tooth.", False),
    "ferrule":           (0.8, "CLIN_FERRULE", "clinical_necessity", "Insufficient ferrule or margin within 3 mm of the crest; crown lengthening is not a CDCP benefit.", False),
    "retired_lab_code":  (0.8, "ADMIN_INVALID_CODE", "administrative", "Laboratory fee code is not valid for the date of service.", True),
    "thin_note":         (0.5, "DOC_INSUFFICIENT_NOTES", "incomplete_submission", "Clinical notes do not describe the condition supporting the proposed service.", True),
}
VAGUE = "The service does not meet the CDCP criteria for this benefit."
NO_PATTERN = (0, "CLIN_NEED_NOT_MET", "clinical_necessity", VAGUE, False)
# A letter that names a documentation gap also lists the document it wants.
MISSING_DOC = {"no_pa": "periapical_radiograph", "stale_pa": "periapical_radiograph", "no_bw": "bitewing_radiographs",
               "no_perio": "periodontal_charting", "thin_note": "clinical_notes"}
BASELINE_DENY = 0.04  # consultant variance: some complete, clinically sound requests are still denied
CONSULTANT_ACTS = 0.8  # share of visible problems a consultant acts on; tuned to the ~37% crown approval rate


def pick(weighted):
    items, weights = zip(*weighted)
    return random.choices(items, weights)[0]


def tooth_class(t: int) -> str:
    return "molar" if t in MOLARS else "premolar" if t in PREMOLARS else "third_molar" if t in THIRD_MOLARS else "anterior"


def clinical_state(submitted: date) -> dict:
    tooth = pick([(random.choice(MOLARS), 0.51), (random.choice(PREMOLARS), 0.3), (random.choice(ANTERIORS), 0.17), (random.choice(THIRD_MOLARS), 0.02)])
    cls = tooth_class(tooth)
    endo = random.random() < (0.5 if cls != "anterior" else 0.35)
    s = {"tooth": tooth, "class": cls, "endo": endo,
         "endo_weeks_ago": (random.choice([3, 4, 5, 6, 8]) if random.random() < 0.12 else random.randint(12, 150)) if endo else None,
         "periapical_lesion": False}
    s["periapical_lesion"] = endo and s["endo_weeks_ago"] < 10 and random.random() < 0.5
    # Structure loss. Endo posterior needs >=3 surfaces incl. both ridges or a lost cusp; non-endo posterior needs 5.
    if cls == "anterior":
        s["incisal_edge_lost"] = random.random() < 0.55
        s["surfaces"] = random.randint(1, 4)
    else:
        s["surfaces"] = pick([(2, 0.07), (3, 0.23), (4, 0.2), (5, 0.5)])
        s["cusp_fractured"] = random.random() < 0.45
    s["indication"] = pick([("fracture", 0.34), ("large_restoration", 0.26), ("post_endo", 0.18 if endo else 0.0),
                            ("recurrent_caries", 0.12), ("cracked_tooth", 0.07), ("cosmetic", 0.04 if cls == "anterior" else 0.0)])
    # Perio: seniors mostly PSR 2-3; about a third have a code-4 sextant somewhere.
    s["psr"] = {sx: pick([(1, 0.15), (2, 0.4), (3, 0.3), (4, 0.15)]) for sx in SEXTANTS}
    local = s["psr"][SEXTANT_OF[tooth]]
    s["pd_mm"] = [max(1, min(9, random.choice([2, 3, 3, 3, 4]) + (local == 4) * random.randint(1, 3))) for _ in range(6)]
    s["bop"] = max(s["pd_mm"]) >= 5 and random.random() < 0.6
    s["bone_loss_pct"] = random.choice([10, 15, 20, 25, 30, 35, 40]) + (local == 4) * random.randint(10, 30)
    s["furcation"] = random.choices([0, 1, 2, 3], [0.75, 0.13, 0.08, 0.04])[0] if cls == "molar" else 0
    s["subgingival_margin"] = random.random() < 0.12
    s["pending_basic"] = [(random.choice(["21211", "21212", "23111", "23112"]), random.choice(MOLARS + PREMOLARS)) for _ in range(random.choices([0, 1, 2, 3], [0.87, 0.08, 0.035, 0.015])[0])]
    if max(s["psr"].values()) == 4 and random.random() < 0.15:
        s["pending_basic"].append(("43421", None))  # scaling/root planing still to do
    s["prior_crown_months"] = random.randint(20, 90) if random.random() < 0.05 else None
    return s


def violations(s: dict, age_band: str, dup: bool, retired: bool) -> set[str]:
    """What is clinically true of the request, whether or not the submission shows it."""
    v = set()
    if age_band == "0-17":
        v.add("age_under_18")
    if s["class"] == "third_molar":
        v.add("third_molar")
    if dup:
        v.add("duplicate")
    if s["prior_crown_months"]:
        v.add("frequency")
    if s["pending_basic"]:
        v.add("pending_basic")
    if s["endo"] and (s["endo_weeks_ago"] < 8 or s["periapical_lesion"]):
        v.add("endo_not_healed")
    if s["class"] == "anterior":
        if not s["incisal_edge_lost"]:
            v.add("not_ext_restored")
    elif not (s["cusp_fractured"] or (s["endo"] and s["surfaces"] >= 3) or s["surfaces"] >= 5):
        v.add("not_ext_restored")
    if s["indication"] in ("cracked_tooth", "cosmetic"):
        v.add("crack_or_cosmetic")
    if max(s["pd_mm"]) >= 5 and s["bop"]:
        v.add("active_perio")
    if s["bone_loss_pct"] > 50:
        v.add("poor_support")
    if s["furcation"] >= 2:
        v.add("furcation")
    if s["subgingival_margin"]:
        v.add("ferrule")
    if retired:
        v.add("retired_lab_code")
    return v


# --- rendering: what the clinic sends -------------------------------------------------------------

SURF = {1: "O", 2: "MO", 3: "MOD", 4: "MODB", 5: "MODBL"}


def render_note(s: dict, style: str, rng=random) -> str:
    t, bits = s["tooth"], []
    if style == "terse" and rng.random() < 0.45:
        return rng.choice([f"#{t} needs crown.", f"Pt wants crown on {t}.", f"{t} crown recommended, see chart.",
                           f"Recommend crown #{t} as discussed.", f"{t} broken, crown."])
    if s["class"] == "anterior":
        bits.append(f"#{t} {'fractured incisal edge, loss extends to both contacts' if s['incisal_edge_lost'] else 'large class IV composite, incisal edge intact'}.")
    else:
        rest = rng.choice(["amalgam", "composite"])
        bits.append(f"#{t} {SURF[s['surfaces']]} {rest}" + (f", {rng.choice(['DL', 'ML', 'DB', 'MB'])} cusp fractured" if s["cusp_fractured"] else "") + ".")
    if s["endo"]:
        wk = s["endo_weeks_ago"]
        bits.append(f"RCT completed {f'{wk} weeks ago' if wk < 12 else f'{wk // 4} months ago' if wk < 104 else 'in ' + str(2026 - wk // 52)}" +
                    (", PA radiolucency still present" if s["periapical_lesion"] and rng.random() < 0.7 else ", asymptomatic") + ".")
    ind = {"fracture": "Tooth fractured, unrestorable with direct restoration.", "large_restoration": "Existing restoration failing, marginal breakdown.",
           "post_endo": "Crown indicated to protect endo-treated tooth.", "recurrent_caries": "Recurrent caries under existing restoration.",
           "cracked_tooth": rng.choice(["Cracked tooth syndrome, pain on biting.", "Craze lines, sensitive to cold."]),
           "cosmetic": rng.choice(["Pt unhappy with shade, wants crown for appearance.", "Discoloured, pt requests crown to improve esthetics."])}
    bits.append(ind[s["indication"]])
    if style == "detailed":
        if s["pending_basic"] and rng.random() < 0.6:
            bits.append("Also " + ", ".join(f"{'SRP' if c == '43421' else 'restore'} {'' if tt is None else '#' + str(tt)}".strip() for c, tt in s["pending_basic"]) + " planned.")
        if s["subgingival_margin"]:
            bits.append(rng.choice(["Decay extends subgingivally, crown lengthening may be required.", "Margin at bone level distally."]))
        if s["furcation"] >= 2 and rng.random() < 0.7:
            bits.append(f"Class {'II' if s['furcation'] == 2 else 'III'} furcation.")
        if s["bone_loss_pct"] > 50 and rng.random() < 0.6:
            bits.append("Moderate-severe bone loss on PA.")
        bits.append(rng.choice(["Tooth vital." if not s["endo"] else "No TTP.", "Occlusion stable.", "Pt informed of options."]))
    return " ".join(bits)


def render_narrative(s: dict, style: str) -> str | None:
    if style != "detailed" or random.random() < 0.4:
        return None
    return (f"Request for crown on #{s['tooth']}. The tooth meets the CDCP definition of extensively restored"
            f"{' following endodontic treatment' if s['endo'] else ''}. All other basic treatment is complete. "
            "Periodontal status is stable at the requested tooth.")  # clinics template this whether or not it is true


def denial_letter(pattern: str | None, rng) -> dict:
    """The reason fields of a denial letter. Clinical letters are often vague, and any letter sometimes is."""
    _, rcode, cat, text, _ = PATTERNS.get(pattern, NO_PATTERN)
    vague = cat == "clinical_necessity" and rng.random() < 0.5 or rng.random() < 0.1
    return {"reason_code": "UNSPECIFIED" if vague else rcode, "reason_category": None if vague else cat,
            "explanation_of_benefits_text": VAGUE if vague else text,
            "missing_documents": [MISSING_DOC[pattern]] if pattern in MISSING_DOC and not vague else []}


def resubmission_changes(fix: str, s: dict, decided: date, resub: date, rng) -> dict:
    """What the clinic sends differently to answer the letter, as a diff on the first request."""
    def since_letter() -> str:
        return str(decided + timedelta(days=rng.randint(1, (resub - decided).days - 1)))
    if fix in ("no_pa", "stale_pa", "endo_not_healed"):  # endo: wait for healing, then a fresh film
        return {"added_attachments": [{"type": "periapical_radiograph", "count": 1, "captured_date": since_letter()}]}
    if fix == "no_bw":
        return {"added_attachments": [{"type": "bitewing_radiographs", "count": 2, "captured_date": since_letter()}]}
    if fix == "no_perio":
        when = since_letter()
        return {"added_attachments": [{"type": "periodontal_charting", "count": 1, "captured_date": when}],
                "perio_summary": {"chart_type": "complete", "captured_date": when, "psr": s["psr"], "tooth_sites_mm": s["pd_mm"],
                                  "bop_at_tooth": s["bop"], "furcation_class": s["furcation"] if s["class"] == "molar" else None}}
    if fix == "pending_basic":
        return {"completed_treatment": [{"code": c, "tooth": t, "date": since_letter()} for c, t in s["pending_basic"]]}
    if fix == "active_perio":  # scaling and root planing, then a re-evaluation chart
        srp, chart = decided + timedelta(days=rng.randint(1, 5)), resub - timedelta(days=rng.randint(0, 3))
        return {"completed_treatment": [{"code": "43421", "tooth": None, "date": str(srp)}],
                "added_attachments": [{"type": "periodontal_charting", "count": 1, "captured_date": str(chart)}]}
    if fix == "retired_lab_code":
        return {"lab_codes": ["99112"]}
    return {"clinical_notes": render_note(s, "standard", rng)}  # thin_note


def make(i: int, clinic: dict, prior: list[dict]) -> dict:
    submitted = date(2026, 4, 1) + timedelta(days=random.randint(0, 170))
    decided = submitted + timedelta(days=random.randint(2, 18))
    code, desc, fee = random.choice(CROWNS)
    age_band = pick(AGE_BANDS)
    tier = random.choice(list(COPAY))
    s = clinical_state(submitted)
    dup = bool(prior) and random.random() < 0.025
    lab = ["99222"] if clinic["stale_fee_table"] and random.random() < 0.7 else ["99112"] if code != "27301" else []
    care = clinic["doc_care"]

    # Attachments: a careful clinic sends the matrix set; others drop, or send what is on file even if old.
    att, sent = [], {}
    if random.random() < 0.72 + 0.27 * care:
        old = random.random() < 0.15 * (1 - care) + 0.02
        sent["pa_date"] = submitted - timedelta(days=random.randint(380, 700) if old else random.randint(3, 120))
        att.append({"type": "periapical_radiograph", "count": 1, "captured_date": str(sent["pa_date"])})
    if random.random() < 0.6 + 0.38 * care:
        sides = 2 if random.random() < 0.93 else 1
        att.append({"type": "bitewing_radiographs", "count": sides, "captured_date": str(submitted - timedelta(days=random.randint(3, 200)))})
        sent["bw"] = sides
    perio = None
    if random.random() < 0.55 + 0.43 * care:
        complete = random.random() < 0.88
        perio = {"chart_type": "complete" if complete else "psr_only", "captured_date": str(submitted - timedelta(days=random.randint(3, 250))),
                 "psr": s["psr"], "tooth_sites_mm": s["pd_mm"] if complete else None, "bop_at_tooth": s["bop"] if complete else None,
                 "furcation_class": s["furcation"] if complete and s["class"] == "molar" else None}
        att.append({"type": "periodontal_charting", "count": 1, "captured_date": perio["captured_date"]})
    style = clinic["note_style"]
    note = render_note(s, style)
    att.append({"type": "clinical_notes", "count": 1, "captured_date": str(submitted - timedelta(days=random.randint(0, 30)))})
    narrative = render_narrative(s, style)
    if narrative:
        att.append({"type": "narrative_letter", "count": 1, "captured_date": str(submitted)})
    if random.random() < 0.3:
        att.append({"type": "tooth_structure_loss_pct", "count": 1, "captured_date": str(submitted)})
    # Pending work shows on the plan only when the clinic sends the whole plan.
    plan = {"pending": [{"code": code, "tooth": s["tooth"]}] + ([{"code": c, "tooth": t} for c, t in s["pending_basic"]] if random.random() < 0.7 else []),
            "completed": [{"code": "01202", "tooth": None}] + ([{"code": "33111", "tooth": s["tooth"], "date": str(submitted - timedelta(weeks=s["endo_weeks_ago"]))}] if s["endo"] else [])} \
        if random.random() < 0.35 + 0.55 * care else None

    truth = violations(s, age_band, dup, lab == ["99222"])
    visible = set(truth)
    # Documentation gaps are visible by definition.
    if "pa_date" not in sent:
        visible.add("no_pa")
    elif (submitted - sent["pa_date"]).days > 365:
        visible.add("stale_pa")
    if "bw" not in sent or sent["bw"] < 2:
        visible.add("no_bw")
    if not perio or perio["chart_type"] != "complete":
        visible.add("no_perio")
    if len(note) < 40 and not narrative:
        visible.add("thin_note")
    # Clinical truths the consultant can only act on if the submission reveals them.
    if "pa_date" not in sent:
        visible -= {"endo_not_healed", "poor_support", "ferrule"} if random.random() < 0.6 else set()
    if not perio or perio["chart_type"] != "complete":
        visible -= {"active_perio", "furcation"} if random.random() < 0.6 else set()
    if not plan and "pending_basic" in visible and random.random() < 0.5:
        visible.discard("pending_basic")  # bitewings may still show the caries
    if narrative and random.random() < 0.3:
        visible -= {"not_ext_restored"}  # a confident narrative sometimes carries it

    fired = [p for p in PATTERNS if p in visible and random.random() < PATTERNS[p][0] * CONSULTANT_ACTS]
    denied = bool(fired) or random.random() < BASELINE_DENY
    rec = {
        "_synthetic": True, "schema": "cdcp-preauth-export/2", "preauth_id": f"PA-SYN-{300000 + i}", "program": "CDCP",
        "administrator": "Sun Life (CDCP administrator)", "submission_channel": clinic["channel"],
        "submitted_date": str(submitted), "decision_date": str(decided),
        "member": {"member_id": f"SYN-M-{random.randint(10**7, 10**8 - 1)}", "age_band": age_band, "province": "ON", "income_band": tier, "copay_pct": COPAY[tier]},
        "provider": {"provider_id": clinic["id"], "specialty": clinic["specialty"], "province": "ON", "cdcp_participating": True},
        "services": [{"procedure_code": code, "description": desc, "category": "major_restorative", "tooth": str(s["tooth"]),
                      "fee_submitted": fee, "fee_grid_amount": round(fee * random.uniform(0.74, 0.86), 2), "lab_codes": lab}],
        "attachments": att, "perio_summary": perio, "treatment_plan": plan, "clinical_notes": note, "narrative": narrative,
        "prior_history": {"same_code_last_5y": bool(s["prior_crown_months"] and s["prior_crown_months"] <= 60),
                          "same_tooth_crown_months_ago": s["prior_crown_months"],
                          "previous_preauth_ids": [random.choice(prior)["preauth_id"]] if dup else []},
    }
    fee_grid = rec["services"][0]["fee_grid_amount"]
    reasons = {"denial_reason": None, "resubmission_denial_reason": None}  # what each letter would name if it weren't vague
    if not denied:
        rec["decision"] = {"status": "approved", "reason_code": None, "reason_category": None,
                           "explanation_of_benefits_text": "Service approved as submitted; payable at CDCP fee grid less applicable co-pay.",
                           "missing_documents": [], "reviewer_type": random.choice(["automated", "dental_consultant"]),
                           "approved_amount": round(fee_grid * (1 - COPAY[tier] / 100), 2), "approval_valid_until": str(decided + timedelta(days=365))}
        rec["followup"] = None
    else:
        main = fired[0] if fired else None
        _, reasons["denial_reason"], cat, _, fixable = PATTERNS.get(main, NO_PATTERN)
        rec["decision"] = {"status": "denied", **denial_letter(main, random),
                           "reviewer_type": "dental_consultant" if cat == "clinical_necessity" else random.choice(["automated", "dental_consultant"])}
        rec["followup"] = None
        if fixable and random.random() < 0.45:
            rest = [p for p in fired[1:] if not PATTERNS[p][4]]
            second = rest[0] if rest else None
            resub = decided + timedelta(days=random.randint(10, 60))
            outcome = "denied" if rest or random.random() < 0.15 else "approved"
            # Own random stream, so adding resubmission detail leaves every other generated value unchanged.
            fu_rng = random.Random(f"{rec['preauth_id']}-resubmission")
            if outcome == "denied":
                reasons["resubmission_denial_reason"] = PATTERNS.get(second, NO_PATTERN)[1]
            rec["followup"] = {"type": "resubmission", "submitted_date": str(resub), "fixed": main,
                               "changes": resubmission_changes(main, s, decided, resub, fu_rng), "outcome": outcome,
                               **(denial_letter(second, fu_rng) if outcome == "denied" else {})}
    rec["_generator_truth"] = {"clinical": {k: v for k, v in s.items() if k != "psr"}, "violations": sorted(truth),
                               "visible_to_consultant": sorted(visible), "fired": fired, **reasons}
    return rec


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    recs: list[dict] = []
    for i in range(N):
        recs.append(make(i, random.choice(CLINICS), recs))
    for r in recs:
        (OUT / f"{r['preauth_id']}.json").write_text(json.dumps(r, indent=2))
    denied = [r for r in recs if r["decision"]["status"] == "denied"]
    vague = sum(r["decision"]["reason_code"] == "UNSPECIFIED" for r in denied)
    incomplete = sum(bool(r["_generator_truth"]["fired"]) and PATTERNS[r["_generator_truth"]["fired"][0]][2] == "incomplete_submission" for r in denied)
    print(f"wrote {N} crown requests to {OUT}: {N - len(denied)} approved ({(N - len(denied)) / N:.0%}), "
          f"{len(denied)} denied; {incomplete / len(denied):.0%} of denials incomplete-submission; {vague / len(denied):.0%} with a vague letter")


if __name__ == "__main__":
    main()
