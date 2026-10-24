"""Generate the five CCAF mock-exam PDFs (ReportLab, A4) from data/question_bank.json."""
import json, os, sys, collections
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Table,
                                TableStyle, KeepTogether, NextPageTemplate, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = "C:/Windows/Fonts/"
pdfmetrics.registerFont(TTFont("Body", FONTS + "arial.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold", FONTS + "arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Body-Italic", FONTS + "ariali.ttf"))
pdfmetrics.registerFont(TTFont("Body-BoldItalic", FONTS + "arialbi.ttf"))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-BoldItalic")
pdfmetrics.registerFont(TTFont("Mono", FONTS + "cour.ttf"))

NAVY = colors.HexColor("#1F3A5F"); GREY = colors.HexColor("#5A6472"); LIGHT = colors.HexColor("#EEF2F7")
GREEN = colors.HexColor("#1B6B3A"); RED = colors.HexColor("#9B2C2C"); AMBER = colors.HexColor("#8A5A00")
RULE = colors.HexColor("#B8C2CF")

S = {}
S["body"] = ParagraphStyle("body", fontName="Body", fontSize=9.6, leading=12.8, textColor=colors.black)
S["small"] = ParagraphStyle("small", parent=S["body"], fontSize=8.4, leading=11, textColor=GREY)
S["h1"] = ParagraphStyle("h1", parent=S["body"], fontName="Body-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=2, spaceAfter=8)
S["h2"] = ParagraphStyle("h2", parent=S["body"], fontName="Body-Bold", fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=8, spaceAfter=4)
S["h3"] = ParagraphStyle("h3", parent=S["body"], fontName="Body-Bold", fontSize=9.8, leading=13, textColor=NAVY, spaceBefore=4, spaceAfter=2)
S["qhead"] = ParagraphStyle("qhead", parent=S["body"], fontName="Body-Bold", fontSize=10, leading=13, textColor=NAVY, spaceBefore=0, spaceAfter=2, keepWithNext=1)
S["pick"] = ParagraphStyle("pick", parent=S["body"], fontName="Body-BoldItalic", fontSize=8.8, leading=11, textColor=AMBER, spaceAfter=2, keepWithNext=1)
S["stem"] = ParagraphStyle("stem", parent=S["body"], spaceAfter=3, keepWithNext=1)
S["opt"] = ParagraphStyle("opt", parent=S["body"], leftIndent=16, firstLineIndent=-16, spaceAfter=1.6)
S["ans"] = ParagraphStyle("ans", parent=S["body"], fontSize=9.2, leading=12.2)
S["optx"] = ParagraphStyle("optx", parent=S["ans"], leftIndent=14, firstLineIndent=0, spaceAfter=2.2)
S["cell"] = ParagraphStyle("cell", parent=S["body"], fontSize=8.4, leading=10.6)
S["cellb"] = ParagraphStyle("cellb", parent=S["cell"], fontName="Body-Bold")
S["cellc"] = ParagraphStyle("cellc", parent=S["cell"], alignment=TA_CENTER)
S["title"] = ParagraphStyle("title", parent=S["body"], fontName="Body-Bold", fontSize=26, leading=31, textColor=colors.white)
S["subtitle"] = ParagraphStyle("subtitle", parent=S["body"], fontSize=13, leading=18, textColor=colors.white)
S["scen"] = ParagraphStyle("scen", parent=S["body"], fontSize=9.2, leading=12.4, textColor=colors.black)
S["toc0"] = ParagraphStyle("toc0", parent=S["body"], fontName="Body-Bold", fontSize=10, leading=15, leftIndent=0)
S["toc1"] = ParagraphStyle("toc1", parent=S["body"], fontSize=9, leading=13, leftIndent=14)

SCEN_TEXT = {
 1: "You are building a customer support resolution agent using the Claude Agent SDK. The agent handles high-ambiguity requests like returns, billing disputes, and account issues. It has access to your backend systems through custom Model Context Protocol (MCP) tools (get_customer, lookup_order, process_refund, escalate_to_human). Your target is 80%+ first-contact resolution while knowing when to escalate.",
 2: "You are using Claude Code to accelerate software development. Your team uses it for code generation, refactoring, debugging, and documentation. You need to integrate it into your development workflow with custom slash commands, CLAUDE.md configurations, and understand when to use plan mode vs direct execution.",
 3: "You are building a multi-agent research system using the Claude Agent SDK. A coordinator agent delegates to specialized subagents: one searches the web, one analyzes documents, one synthesizes findings, and one generates reports. The system researches topics and produces comprehensive, cited reports.",
 4: "You are building developer productivity tools using the Claude Agent SDK. The agent helps engineers explore unfamiliar codebases, understand legacy systems, generate boilerplate code, and automate repetitive tasks. It uses the built-in tools (Read, Write, Bash, Grep, Glob) and integrates with Model Context Protocol (MCP) servers.",
 5: "You are integrating Claude Code into your Continuous Integration/Continuous Deployment (CI/CD) pipeline. The system runs automated code reviews, generates test cases, and provides feedback on pull requests. You need to design prompts that provide actionable feedback and minimize false positives.",
 6: "You are building a structured data extraction system using Claude. The system extracts information from unstructured documents, validates the output using JSON schemas, and maintains high accuracy. It must handle edge cases gracefully and integrate with downstream systems.",
}
SCEN_NAME = {1: "Customer Support Resolution Agent", 2: "Code Generation with Claude Code", 3: "Multi-Agent Research System",
             4: "Developer Productivity with Claude", 5: "Claude Code for Continuous Integration", 6: "Structured Data Extraction"}
DOM_NAME = {1: "Agentic Architecture & Orchestration", 2: "Tool Design & MCP Integration", 3: "Claude Code Configuration & Workflows",
            4: "Prompt Engineering & Structured Output", 5: "Context Management & Reliability"}
DOM_W = {1: 27, 2: 18, 3: 20, 4: 20, 5: 15}
DOM_COUNT = {1: 16, 2: 11, 3: 12, 4: 12, 5: 9}
DIFF_NAME = {"F": "Foundational", "I": "Intermediate", "C": "Challenging"}
TASK_TITLES = {
 "1.1": "Agentic loops for autonomous task execution", "1.2": "Coordinator-subagent orchestration", "1.3": "Subagent invocation, context passing, spawning",
 "1.4": "Multi-step workflows: enforcement and handoff", "1.5": "Agent SDK hooks: interception and normalization", "1.6": "Task decomposition strategies",
 "1.7": "Session state, resumption, and forking", "2.1": "Tool interfaces: descriptions and boundaries", "2.2": "Structured error responses for MCP tools",
 "2.3": "Tool distribution and tool_choice", "2.4": "MCP server integration (Claude Code and agents)", "2.5": "Built-in tools: Read, Write, Edit, Bash, Grep, Glob",
 "3.1": "CLAUDE.md hierarchy, scoping, modularity", "3.2": "Custom slash commands and skills", "3.3": "Path-specific rules", "3.4": "Plan mode vs direct execution",
 "3.5": "Iterative refinement techniques", "3.6": "Claude Code in CI/CD pipelines", "4.1": "Explicit criteria; reducing false positives",
 "4.2": "Few-shot prompting", "4.3": "Structured output via tool use and JSON schemas", "4.4": "Validation, retry, feedback loops", "4.5": "Batch processing (Message Batches API)",
 "4.6": "Multi-instance and multi-pass review", "5.1": "Context management across long interactions", "5.2": "Escalation and ambiguity resolution",
 "5.3": "Error propagation across multi-agent systems", "5.4": "Context in large codebase exploration", "5.5": "Human review workflows; confidence calibration",
 "5.6": "Provenance and uncertainty in multi-source synthesis"}


def P(text, style="body"):
    return Paragraph(text, S[style])


def esc(t):
    return escape(t)


class ExamDoc(BaseDocTemplate):
    def __init__(self, filename, running_title, **kw):
        super().__init__(filename, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=20 * mm, bottomMargin=18 * mm,
                         title=kw.pop("title", running_title), author="CCAF practice materials (original, unofficial)", **kw)
        self.running_title = running_title
        fw, fh = A4[0] - 36 * mm, A4[1] - 38 * mm
        frame = Frame(18 * mm, 18 * mm, fw, fh, id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        cover = Frame(0, 0, A4[0], A4[1], leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="cover")
        self.addPageTemplates([PageTemplate(id="cover", frames=[cover], onPage=lambda c, d: None),
                               PageTemplate(id="main", frames=[frame], onPage=self._decorate)])
        self._key = 0

    def _decorate(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor(RULE); canv.setLineWidth(0.5)
        canv.line(18 * mm, A4[1] - 14 * mm, A4[0] - 18 * mm, A4[1] - 14 * mm)
        canv.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
        canv.setFont("Body", 7.6); canv.setFillColor(GREY)
        canv.drawString(18 * mm, A4[1] - 12 * mm, self.running_title)
        canv.drawRightString(A4[0] - 18 * mm, A4[1] - 12 * mm, "Claude Certified Architect - Foundations (CCAR-F) | original practice material")
        canv.drawString(18 * mm, 10 * mm, "Unofficial practice paper - not produced or endorsed by Anthropic. Not a prediction of any real exam score.")
        canv.drawRightString(A4[0] - 18 * mm, 10 * mm, "Page %d" % doc.page)
        canv.restoreState()

    def beforeDocument(self):
        self._key = 0

    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph) and fl.style.name in ("h1", "h2toc"):
            lvl = 0 if fl.style.name == "h1" else 1
            text = fl.getPlainText()
            key = "bm%d" % self._key; self._key += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=lvl, closed=False)
            self.notify("TOCEntry", (lvl, text, self.page, key))


S["h2toc"] = ParagraphStyle("h2toc", parent=S["h2"])


def cover_page(story, title, subtitle, lines):
    def draw():
        from reportlab.platypus.flowables import Flowable
        class Cover(Flowable):
            def wrap(self, aw, ah): return A4[0], A4[1]
            def draw(self_):
                c = self_.canv
                c.setFillColor(NAVY); c.rect(0, A4[1] * 0.42, A4[0], A4[1] * 0.58, stroke=0, fill=1)
                c.setFillColor(colors.HexColor("#C9A227")); c.rect(0, A4[1] * 0.42 - 3 * mm, A4[0], 3 * mm, stroke=0, fill=1)
                c.setFillColor(colors.white); c.setFont("Body", 11); c.drawString(24 * mm, A4[1] - 34 * mm, "CLAUDE CERTIFIED ARCHITECT - FOUNDATIONS  |  EXAM CODE CCAR-F")
                t = Paragraph(title, S["title"]); w, h = t.wrap(A4[0] - 48 * mm, 100 * mm); t.drawOn(c, 24 * mm, A4[1] - 62 * mm - h)
                st = Paragraph(subtitle, S["subtitle"]); w2, h2 = st.wrap(A4[0] - 48 * mm, 100 * mm); st.drawOn(c, 24 * mm, A4[1] - 70 * mm - h - h2)
                y = A4[1] * 0.42 - 16 * mm
                c.setFillColor(colors.black)
                for ln in lines:
                    p = Paragraph(ln, S["body"]); w3, h3 = p.wrap(A4[0] - 48 * mm, 100 * mm); p.drawOn(c, 24 * mm, y - h3); y -= h3 + 5
        return Cover()
    story.append(draw())
    story.append(NextPageTemplate("main"))
    story.append(PageBreak())


def tbl(data, widths, header=True, zebra=True, fs=8.4, pad=3):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("FONT", (0, 0), (-1, -1), "Body", fs), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, RULE),
          ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONT", (0, 0), (-1, 0), "Body-Bold", fs)]
    if zebra:
        for r in range(1, len(data)):
            if r % 2 == 0: st.append(("BACKGROUND", (0, r), (-1, r), LIGHT))
    t.setStyle(TableStyle(st))
    return t


def pick_text(q):
    n = q["select_count"]
    return "Select ONE answer." if n == 1 else "Select exactly %s answers (choose %d)." % ({2: "TWO", 3: "THREE"}[n], n)


def answer_sheet(story, qs):
    story.append(P("Candidate answer sheet", "h1"))
    story.append(P("Mark your answers here while taking the paper. Cells that do not exist for a question are greyed out. Where a question says "
                   "'Select exactly TWO/THREE', mark exactly that many letters. Do not turn to the answer key until you have finished all 60 questions "
                   "(or the 120 minutes have elapsed).", "small"))
    story.append(Spacer(1, 4))
    story.append(P("Name: ______________________    Date: ______________    Start time: ________    End time: ________", "body"))
    story.append(Spacer(1, 6))

    def half(sub):
        rows = [[P("<b>No.</b>", "cellc"), P("<b>Pick</b>", "cellc")] + [P("<b>%s</b>" % l, "cellc") for l in "ABCDEF"]]
        for q in sub:
            nopt = len(q["options"])
            cells = [P("<b>%d</b>" % q["number"], "cellc"), P(str(q["select_count"]), "cellc")]
            for k, l in enumerate("ABCDEF"):
                cells.append(P("( %s )" % l, "cellc") if k < nopt else P("", "cellc"))
            rows.append(cells)
        t = Table(rows, colWidths=[10 * mm, 10 * mm] + [10.5 * mm] * 6, rowHeights=[6.4 * mm] + [7.3 * mm] * len(sub))
        st = [("GRID", (0, 0), (-1, -1), 0.4, RULE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
              ("LEFTPADDING", (0, 0), (-1, -1), 1), ("RIGHTPADDING", (0, 0), (-1, -1), 1), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]
        for r, q in enumerate(sub, 1):
            for k in range(len(q["options"]), 6):
                st.append(("BACKGROUND", (2 + k, r), (2 + k, r), colors.HexColor("#D9DEE5")))
        t.setStyle(TableStyle(st))
        return t
    outer = Table([[half(qs[:30]), half(qs[30:])]], colWidths=[(A4[0] - 36 * mm) / 2] * 2)
    outer.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(outer)
    story.append(PageBreak())


def build_exam(paper, qs, outpath):
    pid = "%02d" % paper
    scens = sorted({q["scenario"] for q in qs})
    doc = ExamDoc(outpath, "CCAF Mock Exam %s" % pid, title="CCAF Mock Exam %s" % pid)
    story = []
    cover_page(story, "Mock Examination %s" % pid, "Claude Certified Architect - Foundations<br/>60 scenario-based questions | 120 minutes",
               ["<b>Scenarios assessed in this paper:</b> " + "; ".join("Scenario %d - %s" % (s, SCEN_NAME[s]) for s in scens),
                "<b>Format:</b> multiple-choice and multiple-response; every question states how many answers to select.",
                "<b>Contents:</b> instructions and blueprint | candidate answer sheet | 60 questions | quick answer key and score tracker | "
                "detailed explanations for every option | domain-level review guide | revision checklist.",
                "<b>Status:</b> ORIGINAL PRACTICE MATERIAL. This is not an official Anthropic examination paper and contains no confidential exam content. "
                "It was written against the publicly available Claude Certified Architect - Foundations Exam Guide (v1.0, effective July 2026)."])
    toc = TableOfContents(); toc.levelStyles = [S["toc0"], S["toc1"]]
    story.append(P("Contents", "h2")); story.append(toc); story.append(PageBreak())

    # --- instructions / blueprint
    story.append(P("1. Instructions and exam conditions", "h1"))
    story += [P("<b>Time limit: 120 minutes</b> for 60 questions (an average of 2 minutes per question). Work in one sitting, without notes, documentation, or AI assistance, to get a realistic read on your readiness.", "body"), Spacer(1, 4)]
    story += [P("&bull; Every question is anchored to one of the production scenarios in this paper. Read the scenario description at the start of each scenario section; questions are otherwise self-contained.", "body"),
              P("&bull; Each question states <b>how many answers to select</b>. For 'Select ONE', exactly one option is best. For 'Select exactly TWO/THREE', all selected options must be correct; there is no partial credit in this practice format.", "body"),
              P("&bull; Choose the <i>best</i> answer for the stated constraints, not an answer that could merely work. Where a question asks for the FIRST, SAFEST, or MOST RELIABLE step, that qualifier is part of the question.", "body"),
              P("&bull; Attempt every question. Unanswered questions score zero. There is no 'all of the above' or 'none of the above'.", "body"),
              P("&bull; Do not look at the answer key until you have finished. The key, explanations, and review guide begin after Question 60.", "body"), Spacer(1, 8)]
    story.append(P("2. What is verified, what is supplied, and what is original", "h1"))
    story.append(tbl([[P("<b>Category</b>", "cell"), P("<b>What it covers</b>", "cell")],
        [P("Verified official information", "cellb"), P("From the official Exam Guide (CCAR-F v1.0): 60 items; multiple-choice and multiple-response items that state how many responses to select; 4 scenarios drawn from a bank of 6; 120-minute limit; scaled passing score of 720 on a 100-1,000 scale; score report with percent-correct by domain; domain weights 27/18/20/20/15%; the 31 task statements and the in-scope/out-of-scope lists.", "cell")],
        [P("Scenario descriptions", "cellb"), P("The six production scenarios are quoted from the official guide; the extra topic lists you were given (e.g., idempotency, structured handoffs, schema design) guided question themes. Scenario text shown above each question group is the official description.", "cell")],
        [P("Original practice content", "cellb"), P("All questions, options, explanations, and review guidance in this file were written for this pack. They are not official questions, are not copied from commercial practice exams or leaked banks, and may differ in difficulty from the real exam.", "cell")],
        [P("Supplemental knowledge", "cellb"), P("A few items use general engineering knowledge to make a scenario realistic (for example CI/CD terminology or least-privilege shell access). They are flagged 'Supplemental' in the explanation and are not confirmed exam objectives.", "cell")]],
        [38 * mm, A4[0] - 36 * mm - 38 * mm]))
    story.append(Spacer(1, 6))
    story.append(P("A raw percentage on this paper is <b>not</b> a scaled score. The real exam reports a scaled score (100-1,000) with a cut score of 720 derived from a formal standard-setting study; percent-correct by domain is shown for information only. Doing well on these papers does not guarantee a pass.", "body"))
    story.append(PageBreak())
    story.append(P("3. Exam blueprint for this paper", "h1"))
    cnt = collections.Counter(q["primary_domain"] for q in qs)
    rows = [[P("<b>Domain</b>", "cell"), P("<b>Official weight</b>", "cellc"), P("<b>Questions in this paper</b>", "cellc")]]
    for d in range(1, 6):
        rows.append([P("%d. %s" % (d, DOM_NAME[d]), "cell"), P("%d%%" % DOM_W[d], "cellc"), P(str(cnt[d]), "cellc")])
    rows.append([P("<b>Total</b>", "cell"), P("<b>100%</b>", "cellc"), P("<b>%d</b>" % len(qs), "cellc")])
    story.append(tbl(rows, [100 * mm, 32 * mm, 40 * mm]))
    story.append(Spacer(1, 6))
    story.append(P("Question counts are the closest integer allocation of the official weights to 60 questions. Each question has exactly one primary domain; secondary domains appear in the answer key where a question also touches another domain.", "small"))
    story.append(Spacer(1, 8))
    srow = [[P("<b>Scenario</b>", "cell"), P("<b>Questions</b>", "cellc"), P("<b>Numbers</b>", "cellc")]]
    for s in scens:
        ns = [q["number"] for q in qs if q["scenario"] == s]
        srow.append([P("Scenario %d - %s" % (s, SCEN_NAME[s]), "cell"), P(str(len(ns)), "cellc"), P("%d-%d" % (min(ns), max(ns)), "cellc")])
    story.append(tbl(srow, [100 * mm, 32 * mm, 40 * mm]))
    story.append(Spacer(1, 8))
    dif = collections.Counter(q["difficulty"] for q in qs); rt = collections.Counter(q["response_type"] for q in qs)
    story.append(P("Design targets (not claims about the real exam): about 20%% foundational, 55%% intermediate, 25%% challenging. In this paper: %d foundational, %d intermediate, %d challenging. Response types: %d single-answer, %d select-two, %d select-three." %
                   (dif["F"], dif["I"], dif["C"], rt["S"], rt["M2"], rt["M3"]), "small"))
    story.append(PageBreak())
    answer_sheet(story, qs)

    # --- questions
    story.append(P("4. Examination - Questions 1 to 60", "h1"))
    story.append(P("Time allowed: 120 minutes. Start the clock now.", "pick"))
    cur = None
    for q in qs:
        if q["scenario"] != cur:
            cur = q["scenario"]
            story.append(CondPageBreak(60 * mm))
            first_n = q["number"]
            last_n = max(x["number"] for x in qs if x["scenario"] == cur)
            story.append(Paragraph("Scenario %d: %s (Questions %d-%d)" % (cur, esc(SCEN_NAME[cur]), first_n, last_n), S["h2toc"]))
            box = Table([[P(esc(SCEN_TEXT[cur]), "scen")]], colWidths=[A4[0] - 36 * mm])
            box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("BOX", (0, 0), (-1, -1), 0.6, NAVY), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
            story.append(box); story.append(Spacer(1, 6))
        block = [Paragraph("Question %d" % q["number"], S["qhead"]), Paragraph(pick_text(q), S["pick"]), Paragraph(esc(q["stem"]), S["stem"])]
        for o in q["options"]:
            block.append(Paragraph("<b>%s.</b>&nbsp;&nbsp;%s" % (o["letter"], esc(o["text"])), S["opt"]))
        block.append(Spacer(1, 8))
        story.append(KeepTogether(block))
    story.append(P("End of examination. Stop here, then check your answers using the key that follows.", "pick"))
    story.append(PageBreak())

    # --- quick key + tracker
    story.append(P("5. Quick answer key and score tracker", "h1"))
    story.append(P("Mark each question you answered correctly (all required selections, no wrong ones). Then complete the domain tracker below.", "small"))
    story.append(Spacer(1, 4))

    def keyhalf(sub):
        rows = [[P("<b>No.</b>", "cellc"), P("<b>Ans.</b>", "cellc"), P("<b>Domain</b>", "cellc"), P("<b>Scen.</b>", "cellc"), P("<b>Mine</b>", "cellc")]]
        for q in sub:
            rows.append([P(str(q["number"]), "cellc"), P("<b>%s</b>" % ",".join(q["correct"]), "cellc"), P("D%d" % q["primary_domain"], "cellc"), P("S%d" % q["scenario"], "cellc"), P("", "cellc")])
        t = Table(rows, colWidths=[11 * mm, 14 * mm, 14 * mm, 12 * mm, 14 * mm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, RULE), ("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("FONT", (0, 0), (-1, -1), "Body", 8.4),
                               ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        return t
    outer = Table([[keyhalf(qs[:30]), keyhalf(qs[30:])]], colWidths=[(A4[0] - 36 * mm) / 2] * 2)
    outer.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(outer)
    story.append(Spacer(1, 8))
    story.append(P("Domain-level score tracker", "h2"))
    rows = [[P("<b>Domain</b>", "cell"), P("<b>Questions</b>", "cellc"), P("<b>Number list</b>", "cell"), P("<b>My correct</b>", "cellc"), P("<b>% correct</b>", "cellc")]]
    for d in range(1, 6):
        nums = [str(q["number"]) for q in qs if q["primary_domain"] == d]
        rows.append([P("%d. %s" % (d, DOM_NAME[d]), "cell"), P(str(len(nums)), "cellc"), P(", ".join(nums), "cell"), P("", "cellc"), P("", "cellc")])
    rows.append([P("<b>Total</b>", "cell"), P("<b>60</b>", "cellc"), P("", "cell"), P("", "cellc"), P("", "cellc")])
    story.append(tbl(rows, [52 * mm, 20 * mm, 56 * mm, 22 * mm, 22 * mm], zebra=False, pad=5))
    story.append(Spacer(1, 6))
    story.append(P("Interpretation: percent-correct here is a practice signal only. The real exam's pass/fail decision is based on a single scaled score (cut score 720 of 1,000); domain percentages on the real score report are informational.", "small"))
    story.append(PageBreak())

    # --- detailed explanations
    story.append(P("6. Detailed answer key and explanations", "h1"))
    story.append(P("Each entry gives the correct answer, why it is correct, why every other option is wrong, the concept tested, the detail in the scenario that decides the answer, and a production lesson.", "small"))
    story.append(Spacer(1, 4))
    for q in qs:
        head = "Q%d  |  Domain %d: %s  |  Scenario %d: %s" % (q["number"], q["primary_domain"], q["primary_domain_name"], q["scenario"], q["scenario_name"])
        sec = (", secondary: " + ", ".join("D%d" % d for d in q["secondary_domains"])) if q["secondary_domains"] else ""
        meta = "Task statement %s | %s | %s%s" % (q["task_statement"], DIFF_NAME[q["difficulty"]], "Single answer" if q["select_count"] == 1 else "Select %d" % q["select_count"], sec)
        corr = [o for o in q["options"] if o["correct"]]
        items = [Paragraph(esc(head), S["qhead"]), Paragraph(esc(meta), S["small"])]
        items.append(Paragraph("<b>Correct answer: %s</b> - %s" % (", ".join(o["letter"] for o in corr), esc(" / ".join(o["text"] for o in corr))), ParagraphStyle("ca", parent=S["ans"], textColor=GREEN, spaceBefore=3, spaceAfter=3)))
        items.append(Paragraph("<b>Why the correct answer is correct:</b> " + esc(q["why_correct"]), S["ans"]))
        items.append(Spacer(1, 2))
        items.append(Paragraph("<b>Option-by-option:</b>", S["ans"]))
        for o in q["options"]:
            lab, col = ("CORRECT", "#1B6B3A") if o["correct"] else ("INCORRECT", "#9B2C2C")
            items.append(Paragraph("<b>%s.</b> <font color='%s'><b>[%s]</b></font> %s<br/><i>%s</i>" % (o["letter"], col, lab, esc(o["text"]), esc(o["explanation"])), S["optx"]))
        sup = "<b>Note:</b> this item draws partly on <b>supplemental</b> engineering knowledge that is not a confirmed exam objective.<br/>" if "supplemental" in q["key_concept"].lower() or "supplemental" in " ".join(o["explanation"] for o in q["options"]).lower() else ""
        tail = [Paragraph(sup + "<b>Key concept:</b> " + esc(q["key_concept"]), S["ans"]),
                Paragraph("<b>Exam reasoning:</b> " + esc(q["exam_reasoning"]), S["ans"]),
                Paragraph("<b>Production lesson:</b> " + esc(q["production_lesson"]), S["ans"]), Spacer(1, 3)]
        rule = Table([[""]], colWidths=[A4[0] - 36 * mm], rowHeights=[1])
        rule.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE)]))
        story.append(KeepTogether(items[:5]))
        story += items[5:] + tail + [rule, Spacer(1, 6)]
    story.append(PageBreak())

    # --- domain review guide
    story.append(P("7. Domain-level performance review guide", "h1"))
    story.append(P("Use your tracker. A domain below roughly 70% on a paper deserves a focused review before the next paper. Look at the task statements and concepts listed for each domain and re-read the matching sections of the official Exam Guide.", "small"))
    for d in range(1, 6):
        dq = [q for q in qs if q["primary_domain"] == d]
        tasks = collections.OrderedDict()
        for q in dq:
            tasks.setdefault(q["task_statement"], []).append(q["number"])
        story.append(Paragraph("Domain %d - %s (%d%% official weight; %d questions here)" % (d, esc(DOM_NAME[d]), DOM_W[d], len(dq)), S["h2toc"]))
        rows = [[P("<b>Task</b>", "cell"), P("<b>Topic</b>", "cell"), P("<b>Questions</b>", "cell")]]
        for t in sorted(tasks):
            rows.append([P(t, "cellb"), P(esc(TASK_TITLES[t]), "cell"), P(", ".join(map(str, tasks[t])), "cell")])
        story.append(tbl(rows, [14 * mm, 100 * mm, A4[0] - 36 * mm - 114 * mm]))
        lessons = []
        for q in dq:
            if q["production_lesson"] not in lessons: lessons.append(q["production_lesson"])
        story.append(Spacer(1, 3))
        story.append(P("<b>Lessons to carry forward:</b> " + esc(" ".join(lessons[:6])), "small"))
    story.append(PageBreak())
    story.append(P("8. Final revision checklist", "h1"))
    chk = collections.OrderedDict()
    for q in qs:
        chk.setdefault(q["key_concept"].split("(Task")[0].strip().rstrip(".;"), q["number"])
    story.append(P("Tick each item when you can explain it without looking at the key. Items are drawn from the concepts tested in this paper.", "small"))
    story.append(Spacer(1, 3))
    rows = [[P("[   ]", "cellc"), P(esc(c), "cell"), P("Q%d" % n, "cellc")] for c, n in chk.items()]
    story.append(tbl([[P("<b>Done</b>", "cellc"), P("<b>Concept</b>", "cell"), P("<b>First seen</b>", "cellc")]] + rows, [16 * mm, A4[0] - 36 * mm - 38 * mm, 22 * mm]))
    story.append(Spacer(1, 8))
    story.append(P("Before the next paper: classify each wrong answer as (a) knowledge gap, (b) misread of the stem or qualifier, or (c) a plausible-distractor trap. See CCAF_Final_Revision_Guide.pdf for the method.", "body"))
    doc.multiBuild(story)


def main():
    bank = json.load(open(os.path.join(ROOT, "data", "question_bank.json"), encoding="utf-8"))
    papers = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5]
    for p in papers:
        qs = sorted([q for q in bank if q["paper"] == p], key=lambda q: q["number"])
        out = os.path.join(ROOT, "CCAF_Mock_Exam_%02d.pdf" % p)
        build_exam(p, qs, out)
        print("built", out)


if __name__ == "__main__":
    main()
