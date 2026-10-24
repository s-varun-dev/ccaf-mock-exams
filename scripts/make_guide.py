"""Generate CCAF_Final_Revision_Guide.pdf (study and performance guide summarizing the five papers)."""
import json, os, collections
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether, CondPageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from make_pdfs import *  # styles, helpers, ExamDoc

W = A4[0] - 36 * mm

NOTES = {
 1: [("1.1 Agentic loops", "Continue on stop_reason 'tool_use' (run tools, append tool_result for every tool_use ID); stop on 'end_turn'; treat 'max_tokens' as truncation, not completion. The model chooses the next tool; code does not parse prose.",
      "Terminating on text content or phrases; an iteration cap as the primary stop; sending only the newest message (the API is stateless)."),
     ("1.2 Coordinator-subagent", "Hub-and-spoke: the coordinator decomposes, delegates, aggregates, routes information, and handles errors. Select subagents by query complexity; partition scope; refine iteratively until coverage is sufficient.",
      "Subagent-to-subagent calls; always running the full pipeline; blaming downstream agents when the decomposition was narrow."),
     ("1.3 Invocation and context", "Task tool; allowedTools must include \"Task\"; subagents have isolated context and no shared memory; pass complete findings in the prompt, structured to separate content from metadata; parallel subagents via multiple Task calls in one response; prompts state goals and quality criteria.",
      "Assuming inherited history; prompts that prescribe step-by-step procedures; spawning in separate turns for independent work."),
     ("1.4 Enforcement and handoff", "Programmatic prerequisites and gates for financial or identity rules (prompts have a non-zero failure rate). Handoffs carry customer ID, root cause, amounts, recommended action because humans lack the transcript.",
      "Few-shot or stronger wording as the fix for a rule that must always hold; handoffs that say 'customer is upset'."),
     ("1.5 Hooks", "PostToolUse normalizes or trims results before the model sees them; pre-call hooks block or redirect (for example refunds over a threshold). Hooks verify facts themselves.",
      "Gating on a flag the model sets; per-call checks that miss cumulative limits; prompt rules for hard business rules."),
     ("1.6 Decomposition", "Prompt chaining for predictable multi-aspect work; adaptive decomposition for open-ended work; per-file local passes plus a cross-file integration pass.",
      "A fixed checklist for an unknown cause; one giant pass over many files."),
     ("1.7 Sessions", "--resume <name> continues a prior session when its context is mostly valid; tell it which files changed; start fresh with a structured summary when tool results are stale; fork_session branches from a shared baseline (keep branches draft-only if they can cause side effects).",
      "Resuming into stale tool results; assuming a fork copies the repository.")],
 2: [("2.1 Tool interfaces", "Descriptions drive selection: inputs, example queries, edge cases, boundaries versus similar tools. Rename or split overlapping tools. Check system prompts for keyword rules that override descriptions.",
      "Adding more overlapping tools; keyword routing in prompts; one-word descriptions."),
     ("2.2 Error responses", "isError with category (transient, validation, business, permission), retryability, and a human-readable description. Distinguish access failure from valid empty result. Local recovery first; propagate unresolved errors with context.",
      "Generic 'Operation failed'; empty success on failure; retrying non-retryable errors."),
     ("2.3 Tool distribution and tool_choice", "4-5 role-relevant tools per agent; scoped cross-role tools; constrained replacements (load_document for fetch_url). 'auto' may return text; 'any' guarantees a tool call; forced names a tool (use only for the step that must run first, then continue).",
      "Giving every agent every tool; forcing a tool on every turn; relying on 'auto' for guaranteed structure."),
     ("2.4 MCP integration", "Project .mcp.json for shared servers with ${ENV} expansion; ~/.claude.json for personal or experimental; all servers' tools available at once; resources expose catalogs; enrich descriptions so agents do not prefer built-ins; reuse community servers for standard integrations.",
      "Committing secrets; assuming user-level servers are shared; exploration calls for stable catalogs."),
     ("2.5 Built-in tools", "Grep for contents, Glob for paths, Read/Write for whole files, Edit for unique-anchor changes (Read + Write when no unique anchor). Explore incrementally: Grep, Read, follow imports; search every exported name or wrapper.",
      "Glob for content; reading everything up front; global shell replacements.")],
 3: [("3.1 CLAUDE.md", "User (~/.claude/CLAUDE.md, personal), project (shared via version control), directory-level; @import for modular standards; .claude/rules/ for topic files; /memory shows what is loaded.",
      "Putting team rules in a user-level file; one giant file; copying standards instead of importing."),
     ("3.2 Commands and skills", ".claude/commands/ (project, shared) versus ~/.claude/commands/ (personal); skills in .claude/skills/ with SKILL.md frontmatter: context: fork, allowed-tools, argument-hint. Skills are on-demand; CLAUDE.md is always loaded.",
      "Confusing argument-hint with tool restriction; sharing user-level files; loading rare workflows every session."),
     ("3.3 Path-specific rules", ".claude/rules/*.md with YAML paths globs load only when matching files are involved; glob rules beat directory CLAUDE.md for conventions spread across directories (for example **/*.test.*).",
      "Single-level globs that miss nested folders; missing paths so rules load always."),
     ("3.4 Plan mode versus direct", "Plan mode for large, multi-file, architectural, or multi-approach work (Explore subagent isolates discovery); direct execution for clear, well-scoped changes; combine them for migrations.",
      "Planning trivial fixes; executing large restructurings without a design."),
     ("3.5 Iterative refinement", "2-3 concrete input/output examples; tests first then iterate on failures; interview pattern in unfamiliar domains; one message for interacting issues, sequential fixes for independent ones.",
      "Repeating prose with more emphasis; tests derived from the implementation."),
     ("3.6 CI/CD", "-p / --print for non-interactive runs; --output-format json with --json-schema for machine-parseable findings; CLAUDE.md for review criteria and fixtures; independent review instance; prior findings in context to avoid duplicates; existing tests in context.",
      "Interactive invocations in CI; scraping markdown; same-session self-review.")],
 4: [("4.1 Explicit criteria", "Name what to report and what to skip; define severity levels with concrete examples; temporarily disable a high false-positive category to protect trust.",
      "'Be conservative' or 'only high-confidence' as the fix."),
     ("4.2 Few-shot", "2-4 targeted examples for ambiguous cases with reasoning; demonstrate format; contrast acceptable patterns with genuine issues; cover varied document structures.",
      "Dozens of near-identical examples; examples that encode outdated style."),
     ("4.3 Structured output", "tool_use with JSON schema eliminates syntax errors, not semantic errors; nullable fields prevent fabrication; enums with 'other' plus detail and 'unclear'; normalization rules alongside schemas; money as integer minor units or decimal strings plus currency.",
      "Required fields for data that may be absent; trusting schema validity as correctness."),
     ("4.4 Validation and retry", "Retry with the document, the failed output, and the specific error; retries cannot recover absent information; calculated_total versus stated_total; conflict_detected; detected_pattern to analyze dismissals; bound retries then route to review.",
      "Blind retries; defaults that hide missing data."),
     ("4.5 Batch processing", "Message Batches API: 50% savings, up to 24 hours, no latency guarantee, no multi-turn tool calling inside a request, custom_id correlation. Use for non-blocking work; compute worst-case SLA = submission wait + 24 h (plus retries); refine the prompt on a sample first; resubmit only failures.",
      "Batching blocking checks; assuming result order; ignoring the retry path in SLAs."),
     ("4.6 Multi-instance review", "A generator is biased toward its own work; use an independent instance without its reasoning; per-file plus integration passes; confidence per finding, calibrated before routing.",
      "Same-session self-review; three-run consensus that suppresses intermittent true bugs.")],
 5: [("5.1 Conversation context", "Case-facts block for amounts, dates, order numbers, expectations; trim verbose tool output; key findings first with headers; upstream agents return structured facts; send full history on each request.",
      "Progressive summaries of numbers; padding the middle of long inputs."),
     ("5.2 Escalation", "Escalate for explicit human requests (immediately), policy gaps, and inability to progress; resolve when frustrated but capable; ask for identifiers when several records match; clarify before irreversible actions.",
      "Sentiment or self-reported confidence as triggers; guessing among matches."),
     ("5.3 Error propagation", "Structured error context (type, attempted query, partial results, alternatives); local recovery for transient failures; coverage annotations; valid empty results are reportable findings.",
      "Generic statuses; silent suppression; terminating everything on one failure."),
     ("5.4 Codebase exploration", "Scratchpad files for findings; subagents isolate verbose exploration; summaries injected into the next phase; manifests for crash recovery; /compact when context fills.",
      "Trusting a long context to retain specifics; re-running whole jobs after a crash."),
     ("5.5 Human review", "Segment accuracy by document type and field; stratified sampling of high-confidence output; field-level confidence calibrated on labeled data; route ambiguous or contradictory sources to humans.",
      "Relying on an aggregate number; uncalibrated thresholds."),
     ("5.6 Provenance", "Claim-source mappings preserved through synthesis; annotate conflicts with attribution; require dates; render tables for financial data, prose for news, lists for technical findings.",
      "Averaging conflicting values; dropping sources during summarization.")],
}

CHEAT = [
 ("A rule must hold every time (money, identity, compliance)", "Programmatic gate or hook, not a prompt. Check the real quantity (cumulative, ownership), and verify in code."),
 ("Tool is picked wrongly or interchangeably", "First fix descriptions and boundaries; check the system prompt for keyword rules; then split, rename, or reduce the tool set."),
 ("Stale facts after time or code changes", "Fresh session with a structured summary and re-fetched volatile data; if resuming, name the changed files."),
 ("Output is valid JSON but wrong", "Semantic validation: sums, field placement, ranges, provenance. Schemas fix shape only."),
 ("Required information is absent from the source", "Nullable field, null, and routing to review. Retries cannot recover it."),
 ("A failure reads as 'nothing found'", "Return an error with category and retryability; keep valid empty results as successes."),
 ("Review finds nothing in code or reports the same agent produced", "Independent instance with fresh context; per-file plus integration passes."),
 ("Latency-tolerant bulk workload", "Batches (custom_id, no mid-request tools, worst-case SLA); never for blocking checks."),
 ("Too many agents or tools", "Dynamic selection by complexity; scoped tools; one agent is fine for small tasks."),
 ("Subagent output lacks facts or sources", "Pass complete structured findings in its prompt and require claim-source records back."),
 ("Context grows and answers get generic", "Scratchpad, subagent delegation, /compact, structured summaries; keep numbers in a case-facts block."),
 ("Customer wants a human, or policy is silent", "Escalate with a structured handoff. Do not use sentiment or confidence as the trigger."),
]


def build_guide(bank, out):
    doc = ExamDoc(out, "CCAF Final Study and Revision Guide", title="CCAF Final Study and Revision Guide")
    story = []
    cover_page(story, "Final Study and Revision Guide", "Companion to CCAF Mock Exams 01-05<br/>Performance review, error analysis, and domain revision",
               ["<b>Use this guide with:</b> CCAF_Mock_Exam_01.pdf to CCAF_Mock_Exam_05.pdf (300 original questions in total).",
                "<b>Status:</b> ORIGINAL PRACTICE MATERIAL. Not an official Anthropic document; it summarizes the public Exam Guide (CCAR-F v1.0, effective July 2026) and the practice papers.",
                "<b>Honest limits:</b> a raw percentage on these papers is not a scaled score, and no practice material can guarantee a pass."])
    toc = TableOfContents(); toc.levelStyles = [S["toc0"], S["toc1"]]
    story += [P("Contents", "h2"), toc, PageBreak()]

    story.append(P("1. Purpose and honest limits", "h1"))
    story += [P("This guide turns five timed practice papers into a revision plan. It tells you how to read your results, how to separate real knowledge gaps from reading slips, and what to revise next. It also summarizes the official scope so you can check the papers against it.", "body"), Spacer(1, 4),
              P("&bull; The papers are <b>original and unofficial</b>. They follow the public guide's format, domains, and scenarios, but their difficulty is not psychometrically calibrated and may differ from the real exam.", "body"),
              P("&bull; The real exam reports a <b>scaled score from 100 to 1,000 with a cut score of 720</b>, set by a formal standard-setting study (criterion-referenced, not graded against other candidates). A raw percentage here does not convert to that scale. Domain percentages on the real score report are informational; the pass/fail decision uses the total scaled score.", "body"),
              P("&bull; Practice results are signals about your preparation, not predictions. Preparing with these papers alone does not guarantee a pass; combine them with hands-on building, as the official guide recommends.", "body"), Spacer(1, 6)]
    story.append(P("2. Verified official facts (Exam Guide v1.0)", "h1"))
    story.append(tbl([[P("<b>Item</b>", "cell"), P("<b>Official value</b>", "cell")],
        [P("Credential / code", "cell"), P("Claude Certified Architect - Foundations / CCAR-F", "cell")],
        [P("Items and format", "cell"), P("60 items; multiple-choice and multiple-response; each item states how many responses to select", "cell")],
        [P("Structure", "cell"), P("4 scenarios drawn from a bank of 6", "cell")],
        [P("Time limit", "cell"), P("120 minutes (proctored; online or test center)", "cell")],
        [P("Passing score", "cell"), P("Scaled 720 on a 100-1,000 scale; result is pass/fail plus scaled score and percent-correct by domain", "cell")],
        [P("Domain weights", "cell"), P("1 Agentic Architecture & Orchestration 27%; 2 Tool Design & MCP Integration 18%; 3 Claude Code Configuration & Workflows 20%; 4 Prompt Engineering & Structured Output 20%; 5 Context Management & Reliability 15%", "cell")],
        [P("Explicitly out of scope", "cell"), P("Fine-tuning; API authentication, billing, quotas, pricing; hosting MCP servers; computer use; vision; streaming; OAuth and key rotation; cloud-provider configuration; prompt caching internals; tokenization; model benchmarking", "cell")],
        [P("Validity and retakes", "cell"), P("Credential valid 12 months; retake waits of 14, 30, and 90 days after failed attempts; up to four attempts per rolling 12 months", "cell")]],
        [38 * mm, W - 38 * mm]))
    story.append(PageBreak())

    story.append(P("3. Using the five papers as a progressive sequence", "h1"))
    story.append(tbl([[P("<b>Step</b>", "cell"), P("<b>What to do</b>", "cell"), P("<b>Aim</b>", "cell")],
        [P("Paper 1 (diagnostic)", "cellb"), P("Sit it cold, timed, closed-book. Score by domain. Log every miss with an error type (section 6).", "cell"), P("Find baseline strengths and the two weakest domains.", "cell")],
        [P("Revise", "cellb"), P("Use section 7 on your weakest domains and the cross-reference in section 9 to re-read the matching official task statements.", "cell"), P("Close knowledge gaps before testing again.", "cell")],
        [P("Papers 2 and 3", "cellb"), P("Sit each at least two days after revising. Compare domain scores with Paper 1; expect different scenarios (the scenario mix rotates).", "cell"), P("Check transfer to new contexts, not memory of answers.", "cell")],
        [P("Targeted repair", "cellb"), P("Rewrite, in your own words, the rule behind each miss. Re-answer missed items only after 48 hours.", "cell"), P("Convert misses into rules you can apply.", "cell")],
        [P("Paper 4", "cellb"), P("Full simulation: one sitting, 120 minutes, no interruptions, mark-for-review allowed.", "cell"), P("Pacing and stamina.", "cell")],
        [P("Paper 5 (readiness)", "cellb"), P("Sit it after a final revision pass. Treat consistent domain scores above about 75% across Papers 3-5 as a good sign, and any domain under about 65% as a priority.", "cell"), P("Confirm readiness; plan last-week review.", "cell")]],
        [32 * mm, 95 * mm, W - 127 * mm]))
    story.append(Spacer(1, 6))
    story.append(P("The 65% and 75% figures are practice heuristics for these papers, not official cut points. Do not memorize answers: option order differs from any other source, and the real exam uses different questions.", "small"))
    story.append(Spacer(1, 8))
    story.append(P("Paper-by-scenario coverage", "h2"))
    scen_by_paper = {p: collections.Counter(q["scenario"] for q in bank if q["paper"] == p) for p in range(1, 6)}
    rows = [[P("<b>Scenario</b>", "cell")] + [P("<b>P%d</b>" % p, "cellc") for p in range(1, 6)] + [P("<b>Total</b>", "cellc")]]
    for s in range(1, 7):
        rows.append([P("%d. %s" % (s, SCEN_NAME[s]), "cell")] + [P(str(scen_by_paper[p][s]) if scen_by_paper[p][s] else "-", "cellc") for p in range(1, 6)] + [P(str(sum(scen_by_paper[p][s] for p in range(1, 6))), "cellc")])
    story.append(tbl(rows, [70 * mm] + [16 * mm] * 5 + [W - 150 * mm]))
    story.append(PageBreak())

    story.append(P("4. Score tracking worksheet", "h1"))
    story.append(P("Enter the number correct per domain after each paper (questions per domain are the same in every paper: 16, 11, 12, 12, 9).", "small"))
    hdr = [P("<b>Domain</b>", "cell"), P("<b>Max</b>", "cellc")] + [P("<b>P%d</b>" % p, "cellc") for p in range(1, 6)] + [P("<b>Total / %</b>", "cellc")]
    rows = [hdr]
    for d in range(1, 6):
        rows.append([P("%d. %s" % (d, DOM_NAME[d]), "cell"), P(str(DOM_COUNT[d]), "cellc")] + [P("", "cellc")] * 6)
    rows.append([P("<b>Overall</b>", "cell"), P("<b>60</b>", "cellc")] + [P("", "cellc")] * 6)
    story.append(tbl(rows, [62 * mm, 12 * mm] + [14 * mm] * 5 + [W - 144 * mm], zebra=False, pad=6))
    story.append(Spacer(1, 6))
    story.append(P("Reading the table", "h2"))
    story += [P("&bull; <b>Strongest and weakest domains:</b> rank domains by percent correct, but weigh sample size. Domain 5 has only 9 questions per paper, so one question moves it by 11 points. Use totals across papers (45 questions in Domain 5, 80 in Domain 1) before drawing conclusions.", "body"),
              P("&bull; <b>Trend, not a single paper:</b> look for a domain that stays low across two papers (a real gap) versus one that dips once (often a scenario effect).", "body"),
              P("&bull; <b>Weight your effort:</b> Domain 1 is 27% of the real exam and Domain 5 is 15%; a gap in Domain 1 is usually the better use of limited time, all else equal.", "body"),
              P("&bull; <b>Timing:</b> 120 minutes for 60 items is 2 minutes per item. Aim to finish a first pass in about 90 minutes and keep 25-30 minutes for flagged items and multiple-response checks.", "body")]
    story.append(PageBreak())

    story.append(P("5. Practice results (all 300 items): design statistics", "h1"))
    dom = collections.Counter(q["primary_domain"] for q in bank)
    dif = collections.Counter(q["difficulty"] for q in bank)
    rt = collections.Counter(q["response_type"] for q in bank)
    story.append(P("The bank contains %d questions: %d single-answer, %d select-two, and %d select-three. Primary domains: %s. Difficulty labels (design intent): %d foundational, %d intermediate, %d challenging." %
                   (len(bank), rt["S"], rt["M2"], rt["M3"], "; ".join("D%d=%d" % (d, dom[d]) for d in range(1, 6)), dif["F"], dif["I"], dif["C"]), "body"))
    story.append(Spacer(1, 4))
    story.append(P("Difficulty labels were assigned during design and checked by editorial review. They are not derived from candidate response data, so treat them as rough guides.", "small"))
    story.append(Spacer(1, 8))
    story.append(P("Domain by scenario (question counts across all five papers)", "h2"))
    rows = [[P("<b>Domain</b>", "cell")] + [P("<b>S%d</b>" % s, "cellc") for s in range(1, 7)] + [P("<b>Total</b>", "cellc")]]
    for d in range(1, 6):
        c = collections.Counter(q["scenario"] for q in bank if q["primary_domain"] == d)
        rows.append([P("%d. %s" % (d, DOM_NAME[d]), "cell")] + [P(str(c[s]) if c[s] else "-", "cellc") for s in range(1, 7)] + [P(str(sum(c.values())), "cellc")])
    story.append(tbl(rows, [66 * mm] + [14 * mm] * 6 + [W - 150 * mm]))
    story.append(Spacer(1, 4))
    story.append(P("S1 Customer Support; S2 Claude Code generation; S3 Multi-agent research; S4 Developer productivity; S5 CI; S6 Structured extraction.", "small"))
    story.append(PageBreak())

    story.append(P("6. Classifying and diagnosing wrong answers", "h1"))
    story.append(P("For each wrong or guessed item, write one line in the log and assign exactly one primary error type.", "body"))
    story.append(tbl([[P("<b>Type</b>", "cell"), P("<b>What it looks like</b>", "cell"), P("<b>How to tell</b>", "cell"), P("<b>Fix</b>", "cell")],
        [P("K - knowledge gap", "cellb"), P("You could not state the rule, or the key's reasoning is new to you.", "cell"), P("Read only the stem and answer in your own words, without options. If you cannot, it is a gap.", "cell"), P("Re-read the official task statement; build or test the feature; write the rule in one sentence.", "cell")],
        [P("R - reading slip", "cellb"), P("You knew the concept but missed a qualifier (BEST, FIRST, SAFEST), the count in 'Select TWO', or a number in the stem.", "cell"), P("You can explain the key immediately after seeing it, and you can find the missed phrase in the stem.", "cell"), P("Underline qualifiers and counts before reading options; reread the stem last.", "cell")],
        [P("T - plausible-distractor trap", "cellb"), P("You chose an option that is useful in general but wrong under this stem (for example more prompting where a hook is needed).", "cell"), P("You can name a context where your choice would be right, but the stem's constraint rules it out.", "cell"), P("For each trap, write 'works when ..., fails here because ...'.", "cell")],
        [P("A - added assumption", "cellb"), P("You imported a fact not in the stem to justify an option.", "cell"), P("Your reasoning contains 'probably' or 'maybe the system also ...'.", "cell"), P("Use only the stated constraints; if you need an extra assumption, the option is likely a distractor.", "cell")],
        [P("G - guess / second-guess", "cellb"), P("You changed a right answer or chose without reasoning.", "cell"), P("No written reason at the time.", "cell"), P("Mark uncertain items; on review, change an answer only for a concrete new reason.", "cell")]],
        [30 * mm, 48 * mm, 50 * mm, W - 128 * mm]))
    story.append(Spacer(1, 8))
    story.append(P("A quick test to separate a knowledge gap from a reading mistake: cover the options, restate what the stem is really asking in one sentence, and say what the best action would be. If your own answer matches the key, it was a reading or trap error. If it does not, it was a knowledge gap. Count each type per domain: many K entries mean study; many R or T entries mean practice on question technique.", "body"))
    story.append(Spacer(1, 8))
    story.append(P("Wrong-answer log (copy as needed)", "h2"))
    story.append(tbl([[P("<b>Paper-Q</b>", "cellc"), P("<b>Domain / task</b>", "cellc"), P("<b>Type K/R/T/A/G</b>", "cellc"), P("<b>Rule in one sentence</b>", "cell"), P("<b>Recheck date</b>", "cellc")]] + [[P("", "cell")] * 5 for _ in range(7)],
                     [22 * mm, 30 * mm, 26 * mm, W - 100 * mm, 22 * mm], zebra=False, pad=8))
    story.append(PageBreak())

    story.append(P("7. Domain revision notes", "h1"))
    story.append(P("Each row lists what to know and the classic trap seen in the practice items. Cross-check against the official Exam Guide, Section 6.", "small"))
    for d in range(1, 6):
        story.append(Paragraph("Domain %d - %s (%d%%)" % (d, esc(DOM_NAME[d]), DOM_W[d]), S["h2toc"]))
        rows = [[P("<b>Task</b>", "cell"), P("<b>Know this</b>", "cell"), P("<b>Classic traps</b>", "cell")]]
        for t, know, trap in NOTES[d]:
            rows.append([P("<b>%s</b>" % esc(t), "cell"), P(esc(know), "cell"), P(esc(trap), "cell")])
        story.append(tbl(rows, [30 * mm, 90 * mm, W - 120 * mm]))
        story.append(Spacer(1, 4))
    story.append(PageBreak())

    story.append(P("8. Pattern-recognition cheat sheet", "h1"))
    story.append(tbl([[P("<b>If the stem says ...</b>", "cell"), P("<b>Think ...</b>", "cell")]] + [[P(esc(a), "cell"), P(esc(b), "cell")] for a, b in CHEAT], [75 * mm, W - 75 * mm]))
    story.append(Spacer(1, 8))
    story.append(P("Qualifier discipline", "h2"))
    story += [P("&bull; <b>FIRST step</b>: the cheapest action that addresses the stated root cause (often descriptions, criteria, or a gate), not the most elaborate architecture.", "body"),
              P("&bull; <b>SAFEST / MOST RELIABLE</b>: favors deterministic enforcement and least privilege over instructions.", "body"),
              P("&bull; <b>BEST</b>: choose the option that satisfies all stated constraints (latency, cost, safety, ownership), not one that merely works.", "body"),
              P("&bull; <b>Select TWO / THREE</b>: every selected option must be correct. Judge options independently, then count.", "body")]
    story.append(PageBreak())

    story.append(P("9. Cross-reference: official task statements to practice questions", "h1"))
    story.append(P("Use this to find every item (across all papers) that assesses a task statement you want to review. IDs are Paper-Question (for example 3-14 is Paper 3, question 14).", "small"))
    by_task = collections.defaultdict(list)
    for q in bank:
        by_task[q["task_statement"]].append("%d-%d" % (q["paper"], q["number"]))
    rows = [[P("<b>Task</b>", "cell"), P("<b>Topic</b>", "cell"), P("<b>#</b>", "cellc"), P("<b>Questions</b>", "cell")]]
    for t in sorted(by_task, key=lambda x: tuple(int(i) for i in x.split("."))):
        rows.append([P("<b>%s</b>" % t, "cell"), P(esc(TASK_TITLES[t]), "cell"), P(str(len(by_task[t])), "cellc"), P(", ".join(by_task[t]), "cell")])
    story.append(tbl(rows, [13 * mm, 58 * mm, 10 * mm, W - 81 * mm], fs=8))
    story.append(PageBreak())

    story.append(P("10. Final week plan and exam-day checklist", "h1"))
    story.append(tbl([[P("<b>Window</b>", "cell"), P("<b>Focus</b>", "cell")],
        [P("7-5 days before", "cell"), P("Re-do your wrong-answer log. For each domain under about 70%, rebuild one small example: a loop with stop_reason, a hook with a gate, a schema with nullable fields, a path-scoped rule, a batch with custom_id.", "cell")],
        [P("4-3 days before", "cell"), P("Skim section 7 and section 8 twice. Re-sit only the wrong items from Papers 1-3, after a 48-hour gap.", "cell")],
        [P("2 days before", "cell"), P("Light review of out-of-scope list and your personal trap list. Sleep, logistics, and ID check (name must match registration).", "cell")],
        [P("Exam day", "cell"), P("Read each stem fully; underline qualifiers and counts; answer, flag, move on; reserve time at the end; change answers only for a concrete reason.", "cell")]],
        [32 * mm, W - 32 * mm]))
    story.append(Spacer(1, 10))
    story.append(P("Readiness checklist", "h2"))
    for it in ["I can state when to continue and when to stop an agentic loop, and what each stop_reason means.",
               "I can choose between a prompt, a hook, and a gate for a given business rule, and justify it.",
               "I can describe what subagents inherit (nothing) and what a coordinator must pass.",
               "I can write a tool description that separates two similar tools and a structured error with category and retryability.",
               "I can place any instruction at the right scope: user, project, directory, path-scoped rule, skill, or command.",
               "I can choose plan mode or direct execution for a task and explain why.",
               "I can design a schema that avoids fabrication (nullable, enums with 'other' and 'unclear') and add semantic validation.",
               "I can decide when retries help and when they cannot, and bound them.",
               "I can decide between synchronous and batch processing and compute a worst-case SLA, including retries.",
               "I can set up independent and multi-pass review, and measure review quality by segment.",
               "I can describe escalation triggers and why sentiment and self-reported confidence are poor ones.",
               "I can explain provenance, conflict annotation, and coverage gaps in multi-source synthesis."]:
        story.append(P("[   ]&nbsp;&nbsp;" + esc(it), "body"))
    story.append(Spacer(1, 8))
    story.append(P("Good luck. These materials are a rehearsal, not a promise: the strongest preparation is building the systems the exam describes.", "small"))
    doc.multiBuild(story)


def main():
    bank = json.load(open(os.path.join(ROOT, "data", "question_bank.json"), encoding="utf-8"))
    out = os.path.join(ROOT, "CCAF_Final_Revision_Guide.pdf")
    build_guide(bank, out)
    print("built", out)


if __name__ == "__main__":
    main()
