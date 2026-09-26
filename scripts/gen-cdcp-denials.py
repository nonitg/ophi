"""Generate synthetic denied and approved CDCP preauthorization records for the denial-learning demo.

All patients, providers, and IDs are fabricated. Codes/reasons mirror publicly
documented CDCP preauth rules (Sun Life administers CDCP); fee values are illustrative.
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
OUT = FIXTURES / "cdcp_denials"
OUT_APPROVED = FIXTURES / "cdcp_approvals"
N = 60
N_APPROVED = 60
random.seed(42)

# Services CDCP lists as preauth-required, with the documentation Sun Life expects.
PROCEDURES = [
    {"code": "27211", "desc": "Crown, porcelain/ceramic fused to metal", "fee": 1150.00, "category": "major_restorative",
     "required_docs": ["periapical_radiograph", "clinical_notes", "tooth_structure_loss_pct"]},
    {"code": "27201", "desc": "Crown, porcelain/ceramic", "fee": 1210.00, "category": "major_restorative",
     "required_docs": ["periapical_radiograph", "clinical_notes", "tooth_structure_loss_pct"]},
    {"code": "33131", "desc": "Root canal, three canals", "fee": 1320.00, "category": "endodontics",
     "required_docs": ["periapical_radiograph", "clinical_notes", "pulp_vitality_test"]},
    {"code": "33141", "desc": "Root canal, four or more canals", "fee": 1480.00, "category": "endodontics",
     "required_docs": ["periapical_radiograph", "clinical_notes", "pulp_vitality_test"]},
    {"code": "52101", "desc": "Partial denture, maxillary, acrylic base, initial", "fee": 1050.00, "category": "prosthodontics",
     "required_docs": ["panoramic_radiograph", "clinical_notes", "missing_teeth_chart"]},
    {"code": "52201", "desc": "Partial denture, mandibular, cast metal, initial", "fee": 1890.00, "category": "prosthodontics",
     "required_docs": ["panoramic_radiograph", "clinical_notes", "missing_teeth_chart", "abutment_prognosis"]},
    {"code": "11117", "desc": "Scaling, additional units beyond frequency limit", "fee": 320.00, "category": "periodontics",
     "required_docs": ["periodontal_charting", "clinical_notes", "bitewing_radiographs"]},
    {"code": "92441", "desc": "Parenteral conscious sedation (IV)", "fee": 610.00, "category": "sedation",
     "required_docs": ["clinical_notes", "medical_history", "sedation_justification"]},
    {"code": "92221", "desc": "General anesthesia", "fee": 780.00, "category": "sedation",
     "required_docs": ["clinical_notes", "medical_history", "sedation_justification"]},
]

DENIAL_REASONS = [
    ("DOC_MISSING_RADIOGRAPH", "Required radiograph(s) not submitted or not diagnostic.", "incomplete_submission"),
    ("DOC_INSUFFICIENT_NOTES", "Clinical notes do not describe condition supporting the proposed service.", "incomplete_submission"),
    ("DOC_MISSING_PERIO_CHART", "Periodontal charting within last 12 months not provided.", "incomplete_submission"),
    ("CLIN_NEED_NOT_MET", "Documentation does not meet CDCP criteria for clinical necessity.", "clinical_necessity"),
    ("CLIN_ALT_BENEFIT", "A less costly alternative (e.g. large restoration) would restore function.", "clinical_necessity"),
    ("CLIN_POOR_PROGNOSIS", "Tooth/abutment prognosis does not support proposed treatment.", "clinical_necessity"),
    ("FREQ_LIMIT", "Service exceeds CDCP frequency limitation.", "frequency"),
    ("DUPLICATE_REQUEST", "Duplicate of a preauthorization already on file.", "administrative"),
    ("NOT_COVERED", "Service not an eligible benefit under CDCP.", "coverage"),
    ("ELIGIBILITY", "Member not eligible for coverage on proposed date of service.", "eligibility"),
]

PROVINCES = ["ON", "BC", "AB", "QC", "MB", "NS", "SK", "NB"]
AGE_BANDS = ["0-17", "18-64", "65-69", "70-74", "75-86", "87+"]
COPAY_TIERS = {"<70k": 0, "70k-80k": 40, "80k-90k": 60}
SPECIALTIES = ["general_dentist", "general_dentist", "general_dentist", "endodontist", "periodontist", "prosthodontist"]
TEETH = [str(t) for q in (1, 2, 3, 4) for t in range(q * 10 + 1, q * 10 + 8)]  # FDI notation

NOTE_SNIPPETS = {
    "strong": ["Mesial-occlusal-distal fracture with >50% cusp loss, confirmed on PA.",
               "Symptomatic irreversible pulpitis, cold test lingering >30s, percussion positive.",
               "Generalized 5-7mm pockets with BOP, subgingival calculus noted on BW."],
    "weak": ["Pt wants crown.", "Tooth sore.", "Recommend treatment as discussed.", "See chart."],
}


def pick_reason(proc, docs_submitted):
    missing = [d for d in proc["required_docs"] if d not in docs_submitted]
    if missing and random.random() < 0.7:
        if any("radiograph" in d for d in missing):
            return DENIAL_REASONS[0], missing
        if "periodontal_charting" in missing:
            return DENIAL_REASONS[2], missing
        return DENIAL_REASONS[1], missing
    return random.choice(DENIAL_REASONS[3:]), missing


def base_record(preauth_id, proc, docs, note_quality, submitted, decided):
    tier = random.choice(list(COPAY_TIERS))
    province = random.choice(PROVINCES)
    tooth = random.choice(TEETH) if proc["category"] in ("major_restorative", "endodontics") else None
    return {
        "_synthetic": True,
        "preauth_id": preauth_id,
        "program": "CDCP",
        "administrator": "Sun Life (CDCP administrator)",
        "submission_channel": random.choice(["cdanet_eclaim", "provider_portal", "paper"]),
        "submitted_date": str(submitted),
        "decision_date": str(decided),
        "member": {
            "member_id": f"SYN-M-{random.randint(10**7, 10**8 - 1)}",
            "age_band": random.choice(AGE_BANDS),
            "province": province,
            "income_band": tier,
            "copay_pct": COPAY_TIERS[tier],
        },
        "provider": {
            "provider_id": f"SYN-P-{random.randint(1000, 9999)}",
            "specialty": random.choice(SPECIALTIES),
            "province": province,
            "cdcp_participating": True,
        },
        "services": [{
            "procedure_code": proc["code"],
            "description": proc["desc"],
            "category": proc["category"],
            "tooth": tooth,
            "fee_submitted": proc["fee"],
            "fee_grid_amount": round(proc["fee"] * random.uniform(0.72, 0.9), 2),
        }],
        "attachments": [{"type": d, "count": 1} for d in docs],
        "clinical_notes": random.choice(NOTE_SNIPPETS[note_quality]),
    }


def make_record(i):
    proc = random.choice(PROCEDURES)
    submitted = date(2025, 1, 1) + timedelta(days=random.randint(0, 540))
    decided = submitted + timedelta(days=random.randint(5, 42))
    docs = [d for d in proc["required_docs"] if random.random() < 0.65]
    (code, text, category), missing = pick_reason(proc, docs)
    note_quality = "weak" if category in ("incomplete_submission", "clinical_necessity") and random.random() < 0.6 else "strong"
    rec = base_record(f"PA-SYN-{100000 + i}", proc, docs, note_quality, submitted, decided)

    resubmitted = category in ("incomplete_submission", "clinical_necessity") and random.random() < 0.55
    followup = None
    if resubmitted:
        followup = {
            "type": "resubmission" if category == "incomplete_submission" else "reconsideration",
            "submitted_date": str(decided + timedelta(days=random.randint(7, 60))),
            "added_documents": missing or ["narrative_letter"],
            "outcome": random.choices(["approved", "denied"], weights=[7, 3])[0],
        }

    rec.update({
        "prior_history": {
            "same_code_last_5y": category == "frequency" or random.random() < 0.1,
            "previous_preauth_ids": [f"PA-SYN-{100000 + random.randint(0, i)}"] if code == "DUPLICATE_REQUEST" and i else [],
        },
        "decision": {
            "status": "denied",
            "reason_code": code,
            "reason_category": category,
            "explanation_of_benefits_text": text,
            "missing_documents": missing if category == "incomplete_submission" else [],
            "reviewer_type": random.choice(["automated", "dental_consultant"]),
        },
        "followup": followup,
    })
    return rec


def make_approved_record(i):
    proc = random.choice(PROCEDURES)
    submitted = date(2025, 1, 1) + timedelta(days=random.randint(0, 540))
    decided = submitted + timedelta(days=random.randint(3, 30))
    # Approvals usually carry the full doc set and specific notes; a few slip through
    # with one doc missing or thin notes so the model can't learn a trivially clean split.
    docs = list(proc["required_docs"])
    if random.random() < 0.12:
        docs.remove(random.choice(docs))
    note_quality = "weak" if random.random() < 0.1 else "strong"
    rec = base_record(f"PA-SYN-{200000 + i}", proc, docs, note_quality, submitted, decided)
    fee_grid = rec["services"][0]["fee_grid_amount"]
    rec.update({
        "prior_history": {"same_code_last_5y": random.random() < 0.05, "previous_preauth_ids": []},
        "decision": {
            "status": "approved",
            "reason_code": None,
            "reason_category": None,
            "explanation_of_benefits_text": "Service approved as submitted; payable at CDCP fee grid less applicable co-pay.",
            "missing_documents": [],
            "reviewer_type": random.choice(["automated", "dental_consultant"]),
            "approved_amount": round(fee_grid * (1 - rec["member"]["copay_pct"] / 100), 2),
            "approval_valid_until": str(decided + timedelta(days=365)),
        },
        "followup": None,
    })
    return rec


def write_records(out_dir, n, make):
    out_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        rec = make(i)
        (out_dir / f"{rec['preauth_id']}.json").write_text(json.dumps(rec, indent=2))
    print(f"wrote {n} files to {out_dir}")


def main():
    write_records(OUT, N, make_record)
    write_records(OUT_APPROVED, N_APPROVED, make_approved_record)


if __name__ == "__main__":
    main()
