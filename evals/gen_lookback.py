"""Generate the fictional 12-month Look-Back history under cases/lookback/. Run from the repo root:
`.venv/bin/python evals/gen_lookback.py 11`. Deterministic for a given seed; outcomes are what the
clinic recorded, gaps are re-derived by the engine at report time."""

import random, yaml, pathlib, sys
from datetime import date, timedelta
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20260918
random.seed(seed)
out = pathlib.Path("cases/lookback"); out.mkdir(exist_ok=True)
for p in out.glob("*.yaml"): p.unlink()
names = ["Olivia Brennan","Marcus Oyelaran","Sofia Castellano","Henry Whitlock","Amara Nkemelu","Jacob Lindqvist",
 "Priyanka Rao","Thomas Beaulieu","Grace Mwangi","Liam Fitzgerald","Noor Haddad","Ethan Kowalski",
 "Chloe Dubois","Samuel Adeyemi","Isabella Ferreira","Owen MacLeod","Zara Qureshi","Nathan Petrov",
 "Ava Thompson","Daniel Osei","Mia Nakamura","Lucas Moreau","Emma Sinclair","Rohan Mehta",
 "Hannah Goldberg","Felix Andersson","Leila Farahani","Caleb Robinson","Ines Almeida","Jonah Weiss",
 "Aisha Bello","Victor Nguyen","Ruth Abernathy","Kofi Mensah"]
teeth = [16,26,36,46,17,27,37,47,14,15,24,25,34,35,44,45,11,21]
fees = {"27211":1285.00,"27201":985.00,"27301":1120.00}
denial_texts = ["Denied as per the plan criteria.", "Supporting documentation insufficient to assess eligibility criteria.",
 "Required radiographs not received.", "Periodontal charting not provided.", None]
def bws(d, missing_left=False):
    r = [{"view":"BW","side":"right","teeth":[14,15,16,17,44,45,46,47],"date":d}]
    if not missing_left: r.append({"view":"BW","side":"left","teeth":[24,25,26,27,34,35,36,37],"date":d})
    return r
start = date(2025,9,20)
for i, name in enumerate(names):
    sub = start + timedelta(days=int(i * 360/len(names)) + random.randint(0,6))
    tooth = random.choice(teeth); code = random.choice(["27211","27211","27201","27301"])
    exam = sub - timedelta(days=random.randint(20,120))
    roll = random.random()
    plan = [{"pending":[code],"completed":["01202"],"date":str(exam)}]
    if roll < 0.52:
        rads = [{"view":"PA","tooth":tooth,"date":str(exam)}] + bws(str(exam)); perio=[{"date":str(exam),"sites":6,"depth":3}]
        decision = "approved" if random.random() < 0.80 else "denied"; text = random.choice(denial_texts[:2]) if decision=="denied" else None
    elif roll < 0.66:
        rads = [{"view":"PA","tooth":tooth,"date":str(sub - timedelta(days=random.randint(400,1100)))}] + bws(str(exam)); perio=[{"date":str(exam),"sites":6,"depth":3}]
        decision="denied"; text=random.choice([denial_texts[0],denial_texts[2],None])
    elif roll < 0.74:
        rads = [{"view":"PA","tooth":tooth,"date":str(exam)}] + bws(str(exam)); perio=[{"date":str(exam),"sites":4,"depth":3}]
        decision="denied"; text=random.choice([denial_texts[0],denial_texts[3]])
    elif roll < 0.81:
        rads = [{"view":"PA","tooth":tooth,"date":str(exam)}] + bws(str(exam)); perio=[]
        decision="denied"; text=random.choice([denial_texts[0],denial_texts[3],denial_texts[1]])
    elif roll < 0.87:
        rads = [{"view":"PA","tooth":tooth,"date":str(exam)}] + bws(str(exam), missing_left=True); perio=[{"date":str(exam),"sites":6,"depth":3}]
        decision="denied"; text=denial_texts[2]
    else:
        rads = [{"view":"PA","tooth":tooth,"date":str(exam)}] + bws(str(exam)); perio=[{"date":str(exam),"sites":6,"depth":3}]
        decision="denied"; text=denial_texts[0]
    resub = (decision=="denied") and random.random() < 0.55
    d = {"id": f"lb{i+1:02d}", "as_of": str(sub),
      "patient": {"id": f"L{i+1:03d}", "name": name, "dob": str(date(1950+random.randint(0,45), random.randint(1,12), random.randint(1,28)))},
      "provider": {"name":"Dr. Priya Lau","licence":"ON-48213"},
      "treatment": {"code": code, "description": {"27211":"Crown, porcelain fused to metal","27201":"Crown, porcelain/ceramic","27301":"Crown, cast metal"}[code],
                    "tooth": tooth, "planned": str(exam), "fee_cents": int(fees[code]*100)},
      "dentition": {"missing":[18,28,38,48]}, "history": [{"code":"01202","date":str(exam)}],
      "radiographs": rads, "perio_charts": perio, "tx_plans": plan,
      "assertions": [{"criterion":c,"date":str(sub - timedelta(days=1))} for c in
                     ["no_active_perio","crown_root_ratio","no_furcation","margin_3mm","ferrule_1_5mm","mesiodistal_space","no_adjunctive_needed","extensively_restored","active_disease_addressed"]],
      "outcome": {"submitted": str(sub), "decision": decision, "denial_text": text, "resubmitted": resub,
                  "resubmitted_decision": ("approved" if random.random()<0.6 else "denied") if resub else None}}
    (out / f"lb{i+1:02d}.yaml").write_text("# Look-Back history — fictional. Outcome block is what the clinic recorded; gaps are re-derived by the engine.\n" + yaml.safe_dump(d, sort_keys=False, allow_unicode=True))
from colombus.lookback import run_lookback
r = run_lookback()
print(f'seed {seed}: submitted {r.submitted}  denied {r.denied} (${r.denied_dollars:,.0f})  doc-gap {r.denied_with_doc_gap}  never resubmitted {r.never_resubmitted} (${r.never_resubmitted_dollars:,.0f})  approved {r.approved}')
