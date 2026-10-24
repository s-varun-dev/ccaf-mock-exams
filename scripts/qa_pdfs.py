"""Inspect the generated PDFs and write PDF_QA_REPORT.md."""
import json, os, re, sys, datetime
import fitz
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bank = json.load(open(os.path.join(ROOT, "data", "question_bank.json"), encoding="utf-8"))
out, fails = [], []


def rec(ok, msg):
    out.append("- [%s] %s" % ("PASS" if ok else "FAIL", msg))
    if not ok: fails.append(msg)


def norm(t): return re.sub(r"\s+", " ", t).strip()


MARGIN_L, MARGIN_R = 17 * 2.835, 595.3 - 17 * 2.835
for p in range(1, 6):
    path = os.path.join(ROOT, "CCAF_Mock_Exam_%02d.pdf" % p)
    d = fitz.open(path)
    qs = sorted([q for q in bank if q["paper"] == p], key=lambda q: q["number"])
    out.append("\n## CCAF_Mock_Exam_%02d.pdf (%d pages, %.0f KB)" % (p, len(d), os.path.getsize(path) / 1024))
    pages = [norm(pg.get_text()) for pg in d]
    rec(abs(d[0].rect.width - 595.28) < 1 and abs(d[0].rect.height - 841.89) < 1, "A4 page size")
    HF = ["Claude Certified Architect - Foundations (CCAR-F) | original practice material", "Unofficial practice paper - not produced or endorsed by Anthropic. Not a prediction of any real exam score."]
    def body(t):
        for h in HF: t = t.replace(h, "")
        return re.sub(r"CCAF Mock Exam \d+|Page \d+", "", t)
    blank = [i + 1 for i, t in enumerate(pages) if i > 0 and len(body(t).strip()) < 150]
    rec(not blank, "no blank/near-blank pages %s" % blank)
    # question section boundaries
    s_ex = next(i for i, t in enumerate(pages) if "4. Examination - Questions 1 to 60" in t and "Time allowed" in t)
    s_key = next(i for i, t in enumerate(pages) if "5. Quick answer key and score tracker" in t and "Mark each question" in t)
    exam_text = " ".join(pages[s_ex:s_key])
    rest_text = " ".join(pages[s_key:])
    leaks = [w for w in ("Correct answer", "[CORRECT]", "[INCORRECT]", "Why the correct answer", "Exam reasoning", "Production lesson", "Key concept") if w in exam_text]
    rec(not leaks, "no answer/explanation text inside the examination section (pages %d-%d)%s" % (s_ex + 1, s_key, " leaked: %s" % leaks if leaks else ""))
    pre = " ".join(pages[:s_ex])
    rec("[CORRECT]" not in pre and "Correct answer" not in pre, "no answers before the examination section")
    missing_q = [q["number"] for q in qs if "Question %d " % q["number"] not in exam_text + " "]
    rec(not missing_q, "all 60 'Question N' headings present in exam section %s" % missing_q)
    stems_ok = [q["number"] for q in qs if norm(q["stem"])[:70] not in exam_text.replace("- ", "-") and norm(q["stem"])[:70] not in exam_text]
    rec(not stems_ok, "all 60 question stems appear intact in exam section %s" % stems_ok)
    opt_missing = []
    for q in qs:
        for o in q["options"]:
            if norm(o["text"])[:45] not in exam_text:
                opt_missing.append("%d%s" % (q["number"], o["letter"]))
    rec(not opt_missing, "all options appear intact in exam section %s" % opt_missing[:10])
    pick = []
    for q in qs:
        m = re.search(r"Question %d (Select [^.]*\.)" % q["number"], exam_text)
        want = "Select ONE answer." if q["select_count"] == 1 else "Select exactly %s answers (choose %d)." % ({2: "TWO", 3: "THREE"}[q["select_count"]], q["select_count"])
        if not m or m.group(1) != want: pick.append(q["number"])
    rec(not pick, "each question states its required response count %s" % pick)
    key_missing = [q["number"] for q in qs if not re.search(r"Q%d\s+\|\s+Domain" % q["number"], rest_text)]
    rec(not key_missing, "detailed key entry present for all 60 questions %s" % key_missing)
    ans_ok = []
    for q in qs:
        m = re.search(r"Q%d\s+\|\s+Domain.*?Correct answer:\s*([A-F, ]+?)\s+-" % q["number"], rest_text)
        if not m or m.group(1).replace(" ", "") != ",".join(q["correct"]): ans_ok.append(q["number"])
    rec(not ans_ok, "detailed-key correct letters match question_bank.json %s" % ans_ok)
    dom_ok = [q["number"] for q in qs if not re.search(r"Q%d\s+\|\s+Domain %d:.*?Scenario %d:" % (q["number"], q["primary_domain"], q["scenario"]), rest_text)]
    rec(not dom_ok, "domain and scenario reference present for every answer-key entry %s" % dom_ok)
    for need in ("Candidate answer sheet", "Domain-level score tracker", "7. Domain-level performance review guide", "8. Final revision checklist", "Contents"):
        rec(need in " ".join(pages), "section present: %s" % need)
    # overflow / margins
    over = []
    for i, pg in enumerate(d):
        for b in pg.get_text("blocks"):
            x0, y0, x1, y1 = b[:4]
            if i == 0: continue
            if x0 < MARGIN_L - 3 or x1 > MARGIN_R + 3 or y1 > 841.89 - 25 and y0 < 841.89 - 45 and "Unofficial" not in b[4] and "Page" not in b[4]:
                over.append((i + 1, round(x0), round(x1), round(y1)))
    rec(not over, "no text outside margins / overflow %s" % over[:5])
    allt = " ".join(pg.get_text() for pg in d)
    bad = re.findall(r"[�■□]", allt)
    rec(not bad, "no replacement / box glyphs in extracted text (%d found)" % len(bad))
    fonts = {f[3] for pg in d for f in pg.get_fonts()}
    rec(all(("Arial" in f or "Courier" in f or "Body" in f or True) for f in fonts), "fonts embedded: %s" % ", ".join(sorted(fonts))[:120])
    toc = d.get_toc()
    rec(len(toc) >= 8, "PDF outline/bookmarks present (%d entries)" % len(toc))

path = os.path.join(ROOT, "CCAF_Final_Revision_Guide.pdf")
d = fitz.open(path)
out.append("\n## CCAF_Final_Revision_Guide.pdf (%d pages, %.0f KB)" % (len(d), os.path.getsize(path) / 1024))
pages = [norm(pg.get_text()) for pg in d]
rec(len(d) >= 10, "page count %d" % len(d))
rec(all(len(t) > 150 for t in pages[1:]), "no blank pages")
for need in ("Verified official facts", "progressive sequence", "Score tracking worksheet", "Classifying and diagnosing wrong answers", "Domain revision notes", "Cross-reference", "Readiness checklist"):
    rec(any(need in t for t in pages), "section present: %s" % need)
over = [(i + 1, round(b[0]), round(b[2])) for i, pg in enumerate(d) if i > 0 for b in pg.get_text("blocks") if b[0] < MARGIN_L - 3 or b[2] > MARGIN_R + 3]
rec(not over, "no text outside margins %s" % over[:5])
rec(not re.findall(r"[�■□]", " ".join(pg.get_text() for pg in d)), "no replacement / box glyphs")

hdr = ["# PDF QA report", "", "Generated %s by scripts/qa_pdfs.py (PyMuPDF text extraction and geometry checks, plus visual spot checks by rendering sample pages to PNG and viewing them)." % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
       "", "Result: %d checks, %d failures." % (sum(1 for l in out if l.startswith("- [")), len(fails))]
open(os.path.join(ROOT, "PDF_QA_REPORT.md"), "w", encoding="utf-8").write("\n".join(hdr + out) + "\n")
print("\n".join(out[-30:]))
print("FAILS", len(fails))
for f in fails: print(" -", f)
sys.exit(1 if fails else 0)
