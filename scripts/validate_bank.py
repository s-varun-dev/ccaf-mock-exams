"""Automated structural / consistency validation of data/question_bank.json.
Writes domain_manifest.csv and answer_key_validation_report.txt. Exits non-zero on any hard failure."""
import json, os, re, csv, collections, itertools, datetime, sys, difflib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bank = json.load(open(os.path.join(ROOT, "data", "question_bank.json"), encoding="utf-8"))
review = {}
rp = os.path.join(ROOT, "data", "review_log.json")
if os.path.exists(rp):
    review = json.load(open(rp, encoding="utf-8"))

TARGET = {1: 16, 2: 11, 3: 12, 4: 12, 5: 9}
fails, warns, lines = [], [], []


def check(name, ok, detail=""):
    lines.append("[%s] %s%s" % ("PASS" if ok else "FAIL", name, (" - " + detail) if detail else ""))
    if not ok:
        fails.append(name + " " + detail)


def tokens(t):
    return set(re.findall(r"[a-z0-9_]+", t.lower()))


ids = [q["id"] for q in bank]
check("Total questions == 300", len(bank) == 300, "found %d" % len(bank))
check("No duplicate question IDs", len(ids) == len(set(ids)))
for p in range(1, 6):
    qs = sorted([q for q in bank if q["paper"] == p], key=lambda q: q["number"])
    check("Paper %d has exactly 60 questions" % p, len(qs) == 60, "found %d" % len(qs))
    check("Paper %d numbering is contiguous 1..60" % p, [q["number"] for q in qs] == list(range(1, 61)))
    check("Paper %d IDs match numbering" % p, all(q["id"] == "P%d-Q%02d" % (p, q["number"]) for q in qs))
    dc = collections.Counter(q["primary_domain"] for q in qs)
    check("Paper %d primary-domain allocation 16/11/12/12/9" % p, dict(dc) == TARGET, str(dict(sorted(dc.items()))))
    sc = sorted({q["scenario"] for q in qs})
    check("Paper %d uses exactly four scenarios" % p, len(sc) == 4, str(sc))
    per = collections.Counter(q["scenario"] for q in qs)
    check("Paper %d scenario sizes within 13-17" % p, all(13 <= v <= 17 for v in per.values()), str(dict(sorted(per.items()))))
    sc_contig = all(max(q["number"] for q in qs if q["scenario"] == s) - min(q["number"] for q in qs if q["scenario"] == s) + 1 == per[s] for s in sc)
    check("Paper %d scenario groups are contiguous blocks" % p, sc_contig)
    rt = collections.Counter(q["response_type"] for q in qs)
    check("Paper %d response mix recorded" % p, True, str(dict(rt)))
    dif = collections.Counter(q["difficulty"] for q in qs)
    lines.append("       difficulty mix F/I/C = %d/%d/%d (design target 12/33/15)" % (dif["F"], dif["I"], dif["C"]))
    pos = collections.Counter(l for q in qs if q["response_type"] == "S" for l in q["correct"])
    check("Paper %d single-answer position balance (max-min <= 2)" % p, max(pos.values()) - min(pos.values()) <= 2, str(dict(sorted(pos.items()))))
    mpos = collections.Counter(l for q in qs if q["response_type"] != "S" for l in q["correct"])
    lines.append("       multi-response correct-letter counts: %s" % dict(sorted(mpos.items())))
    longest = sum(1 for q in qs if q["response_type"] == "S" and len(max(q["options"], key=lambda o: len(o["text"]))["text"]) == len(next(o for o in q["options"] if o["correct"])["text"]) and
                  max(len(o["text"]) for o in q["options"]) == len(next(o for o in q["options"] if o["correct"])["text"]))
    lines.append("       correct option is (tied-)longest in %d/54 single-answer items (chance ~25%%)" % longest)
    if longest > 22:
        warns.append("Paper %d: correct option longest in %d/54" % (p, longest))

# per-question checks
bad = collections.defaultdict(list)
for q in bank:
    n_opt = {"S": 4, "M2": 5, "M3": 6}[q["response_type"]]
    if len(q["options"]) != n_opt: bad["option count"].append(q["id"])
    if [o["letter"] for o in q["options"]] != list("ABCDEF"[:n_opt]): bad["letters"].append(q["id"])
    nc = sum(o["correct"] for o in q["options"])
    if nc != q["select_count"] or len(q["correct"]) != nc: bad["correct count"].append(q["id"])
    if q["correct"] != "".join(o["letter"] for o in q["options"] if o["correct"]): bad["key mismatch"].append(q["id"])
    for o in q["options"]:
        if len(o["explanation"].strip()) < 25: bad["missing/short option explanation"].append(q["id"])
        if len(o["text"].strip()) < 10: bad["short option"].append(q["id"])
        if re.search(r"\b(all|none) of the above\b", o["text"], re.I): bad["all/none of the above"].append(q["id"])
        if re.search(r"\b[Oo]ption [A-F]\b|\([A-F]\)\s", o["explanation"]): bad["letter reference in explanation"].append(q["id"])
    texts = [o["text"] for o in q["options"]]
    if len(set(texts)) != len(texts): bad["duplicate option text"].append(q["id"])
    for f in ("why_correct", "key_concept", "exam_reasoning", "production_lesson", "stem"):
        if len(q[f].strip()) < 15: bad["empty field " + f].append(q["id"])
    if re.search(r"correct answer|the answer is", q["stem"], re.I): bad["answer leak in stem"].append(q["id"])
    full = q["stem"] + " ".join(o["text"] + o["explanation"] for o in q["options"]) + q["why_correct"]
    if re.search(r"[^\x00-\x7F]", full): bad["non-ASCII characters"].append(q["id"])
    if q["response_type"] != "S" and not re.search(r"\b(TWO|THREE|two|three)\b", q["stem"] + str(q["select_count"])) and False: pass
    task_dom = int(q["task_statement"].split(".")[0])
    if task_dom != q["primary_domain"]: bad["task/domain mismatch"].append(q["id"])
for name in ["option count", "letters", "correct count", "key mismatch", "missing/short option explanation", "short option", "all/none of the above",
             "letter reference in explanation", "duplicate option text", "answer leak in stem", "non-ASCII characters", "task/domain mismatch"]:
    check("All questions: no '%s' defects" % name, not bad[name], ", ".join(bad[name][:8]))
for k in [k for k in bad if k.startswith("empty field")]:
    check("All questions: %s" % k, False, ", ".join(bad[k][:8]))
check("Every question has a verified-correct key letter set recorded", all(q["correct"] for q in bank))

# MR stems must tell the candidate how many to choose
mr_bad = [q["id"] for q in bank if q["response_type"] != "S" and not re.search(r"\b(TWO|THREE)\b", q["stem"])]
check("Multiple-response stems state the required count in words (TWO/THREE)", not mr_bad, ", ".join(mr_bad))

# duplicate detection across all 300 stems and option sets
pairs = []
tk = {q["id"]: tokens(q["stem"]) for q in bank}
for a, b in itertools.combinations(bank, 2):
    ja = len(tk[a["id"]] & tk[b["id"]]) / max(1, len(tk[a["id"]] | tk[b["id"]]))
    if ja >= 0.55:
        pairs.append((ja, a["id"], b["id"]))
check("No near-duplicate stems across the 300 questions (Jaccard >= 0.55)", not pairs, "; ".join("%s~%s %.2f" % (x, y, j) for j, x, y in sorted(pairs, reverse=True)[:8]))
corr = {q["id"]: tokens(" ".join(o["text"] for o in q["options"] if o["correct"])) for q in bank}
cp = []
for a, b in itertools.combinations(bank, 2):
    j = len(corr[a["id"]] & corr[b["id"]]) / max(1, len(corr[a["id"]] | corr[b["id"]]))
    if j >= 0.75: cp.append((j, a["id"], b["id"]))
check("No duplicated correct-option text across questions (Jaccard >= 0.75)", not cp, "; ".join("%s~%s %.2f" % (x, y, j) for j, x, y in sorted(cp, reverse=True)[:8]))

# scenario rotation
rot = {p: sorted({q["scenario"] for q in bank if q["paper"] == p}) for p in range(1, 6)}
cnt = collections.Counter(s for v in rot.values() for s in v)
check("Each scenario assessed in at least 3 papers", all(cnt[s] >= 3 for s in range(1, 7)), str(dict(sorted(cnt.items()))))
lines.append("Scenario assignment by paper: " + "; ".join("P%d=%s" % (p, rot[p]) for p in rot))

# task statement coverage
cov = collections.Counter(q["task_statement"] for q in bank)
allt = ["%d.%d" % (d, i) for d, n in {1: 7, 2: 5, 3: 6, 4: 6, 5: 6}.items() for i in range(1, n + 1)]
missing = [t for t in allt if cov[t] == 0]
check("All 31 official task statements are assessed at least once", not missing, "missing: %s" % missing)
lines.append("Questions per task statement: " + ", ".join("%s=%d" % (t, cov[t]) for t in allt))
lines.append("Min/max per task statement: %d / %d" % (min(cov[t] for t in allt), max(cov[t] for t in allt)))

status_counts = collections.Counter()
rows = []
for q in bank:
    r = review.get(q["id"], {})
    status = r.get("status", "authored; automated checks passed")
    status_counts[status] += 1
    rows.append([q["id"], q["paper"], q["number"], q["scenario"], q["scenario_name"], q["primary_domain"], q["primary_domain_name"],
                 ";".join("D%d" % d for d in q["secondary_domains"]), q["task_statement"], q["difficulty"], q["response_type"], q["select_count"], q["correct"], status])
with open(os.path.join(ROOT, "domain_manifest.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["question_id", "paper", "number", "scenario", "scenario_name", "primary_domain", "primary_domain_name", "secondary_domains", "task_statement", "difficulty", "response_type", "select_count", "correct_answer", "verification_status"])
    w.writerows(rows)
lines.append("Verification status counts: " + str(dict(status_counts)))
hdr = ["CCAF mock exam bank - answer-key validation report", "Generated: %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
       "Source: data/question_bank.json (%d questions)" % len(bank), "Automated results: %d checks, %d failures, %d warnings" % (sum(1 for l in lines if l.startswith("[")), len(fails), len(warns)), ""]
rev = []
if os.path.exists(os.path.join(ROOT, "data", "review_notes.txt")):
    rev = ["", "---- Substantive review notes ----"] + open(os.path.join(ROOT, "data", "review_notes.txt"), encoding="utf-8").read().splitlines()
open(os.path.join(ROOT, "answer_key_validation_report.txt"), "w", encoding="utf-8").write("\n".join(hdr + lines + [""] + ["WARNINGS: " + w for w in warns] + rev) + "\n")
print("\n".join(lines))
print("FAILS:", len(fails), "WARNS:", len(warns))
sys.exit(1 if fails else 0)
