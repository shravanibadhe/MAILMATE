"""Runs MailMate's NLP analysis on dataset/email_dataset.csv and prints metrics."""
import csv, json, os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import analyze

rows = list(csv.DictReader(open(os.path.join(os.path.dirname(__file__), "email_dataset.csv"), encoding="utf-8")))
res = []
for r in rows:
    a = analyze(r["email"])
    ex_date, ex_time, ex_ref = r["date"], r["time"], r["reference"].lstrip("#")
    dates = [x.lower() for x in a["entities"]["dates"]]
    times = [x.lower() for x in a["entities"]["times"]]
    res.append(dict(
        level=r["level"], exp=r["intent"], got=a["intent"],
        sent_ok=a["sentiment"] == r["sentiment"],
        urg_ok=a["urgent"] == (r["urgent"] == "yes"),
        sender_ok=a["sender"].lower() == r["sender"].lower(),
        date_ok=(not ex_date) or any(ex_date.lower() in d for d in dates),
        time_ok=(not ex_time) or any(ex_time.lower() in t for t in times),
        ref_ok=(not ex_ref) or a["reference"].lower() == ex_ref.lower(),
        has_date=bool(ex_date), has_time=bool(ex_time), has_ref=bool(ex_ref)))

def acc(x): return round(100 * sum(x) / len(x), 1) if x else 0
out = {"total": len(res)}
out["intent_acc_all"] = acc([r["exp"] == r["got"] for r in res])
for lv in ("standard", "hard"):
    s = [r for r in res if r["level"] == lv]
    out[f"intent_acc_{lv}"] = acc([r["exp"] == r["got"] for r in s]); out[f"n_{lv}"] = len(s)
out["sentiment_acc"] = acc([r["sent_ok"] for r in res])
out["urgency_acc"] = acc([r["urg_ok"] for r in res])
out["sender_acc"] = acc([r["sender_ok"] for r in res])
out["date_acc"] = acc([r["date_ok"] for r in res if r["has_date"]])
out["time_acc"] = acc([r["time_ok"] for r in res if r["has_time"]])
out["ref_acc"] = acc([r["ref_ok"] for r in res if r["has_ref"]])
labels = ["meeting", "interview", "leave", "complaint", "payment", "order", "application", "event", "thanks", "general"]
per = {}
for l in labels:
    tp = sum(1 for r in res if r["exp"] == l and r["got"] == l)
    fp = sum(1 for r in res if r["exp"] != l and r["got"] == l)
    fn = sum(1 for r in res if r["exp"] == l and r["got"] != l)
    p = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * p * rc / (p + rc) if p + rc else 0
    per[l] = dict(support=tp + fn, precision=round(p * 100, 1), recall=round(rc * 100, 1), f1=round(f1 * 100, 1))
out["per_class"] = per
cm = defaultdict(Counter)
for r in res: cm[r["exp"]][r["got"]] += 1
out["confusion"] = {a: {b: cm[a][b] for b in labels} for a in labels}
out["errors"] = [(r["exp"], r["got"]) for r in res if r["exp"] != r["got"]]
json.dump(out, open(os.path.join(os.path.dirname(__file__), "results.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k not in ("confusion",)}, indent=1))
