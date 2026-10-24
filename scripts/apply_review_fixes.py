"""Apply reviewer-driven wording fixes to question sources (each old string must match exactly once)."""
import os, sys
Q = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "questions")
FIXES = [
 # ---- Paper 2
 ("p2_d.py", "Split the generic tool into purpose-specific tools such as extract_data_points, summarize_content, and verify_claim_against_source, each with a defined contract.",
             "Split the overlapping responsibilities into purpose-specific tools (for example extract_invoice_fields and parse_layout_to_text), each with a defined input and output contract."),
 ("p2_d.py", "Merge the two tools into one extract_financial_document tool with a type enum the model fills in.",
             "Merge the two tools into one extract_financial_document tool with a type enum and a one-line description."),
 ("p2_d.py", "Merging hides the distinction without clarifying it.",
             "The model still gets no guidance on what counts as an invoice versus a receipt, so the same edge cases are misrouted inside the merged tool."),
 ("p2_b.py", "so developers are prompted for the required parameter.", "so developers are shown the required parameter when they invoke the skill."),
 ("p2_a.py", "The agent has no record of earlier labels, and the criteria are still vague.",
             "Comparing with earlier labels needs memory the classifier may not have, and the criteria stay vague."),
 ("p2_c.py", "The field is already present and an integer; the problem is its value, which the schema cannot judge.",
             "Even a required positive integer can still point outside the diff; the problem is its value, which the schema cannot judge."),
 # ---- Paper 1
 ("p1_a.py", "In a pre-call hook for process_refund, load the order", "In a PreToolUse hook for process_refund, load the order"),
 ("p1_c.py", "and prompt developers for the endpoint name if invoked", "and prompt developers for the endpoint name if invoked") if False else ("p1_c.py", "Frontmatter that sets allowed-tools to Read and Write only, and an argument-hint such as [endpoint-name].", "Frontmatter that sets allowed-tools to Read and Write only, and an argument-hint such as [endpoint-name] showing the expected argument."),
 ("p1_c.py", "allowed-tools restricts tool access during the skill, and argument-hint prompts for the required parameter.", "allowed-tools limits the tools the skill is granted, and argument-hint tells the developer which argument to supply."),
 ("p1_d.py", "Delete one of the tools and route all requests through the remaining one with a type parameter.", "Delete one of the tools and route all requests through the remaining one, keeping its generic description."),
 ("p1_d.py", "Merging could work, but it discards the opportunity for clear boundaries and may reduce reliability for different input types.", "Consolidating without clarifying inputs, outputs, and boundaries leaves the model's selection problem unsolved."),
 ("p1_d.py", "the coordinator to invoke them. Without it", "the coordinator to invoke them. Without it") if False else ("p1_d.py", "so it can spawn subagents. When the coordinator", "so it can spawn subagents. When the coordinator") if False else ("p1_d.py", "Add \\\"Task\\\" to the coordinator's allowedTools so it can spawn subagents.", "Add \\\"Task\\\" (the subagent-spawning tool) to the coordinator's allowedTools so it can spawn subagents."),
 ("p1_b.py", "This works but is not shared via version control. New engineers must replicate the setup manually and configurations drift.", "This is not shared via version control, so engineers do not get the servers when they clone; setup must be replicated by hand and configurations drift."),
 # ---- Paper 3
 ("p3_c.py", "Combine all three into one message because sending issues together is always faster.", "Combine all three into one message so Claude sees the whole CI report at once and can plan the fixes together."),
 ("p3_c.py", "How should you give feedback to Claude Code to fix them?", "You want each fix verified and committed independently. How should you give feedback to Claude Code to fix them?"),
 ("p3_d.py", "A pre-call hook (or tool-level check) on create_record that looks up the invoice's natural key and blocks or redirects duplicates deterministically.",
             "A pre-call hook or tool-level check on create_record that enforces uniqueness atomically on the invoice's natural key (for example a unique constraint) and redirects duplicates."),
 ("p3_d.py", "Correct. A deterministic check on the outgoing call prevents duplicates regardless of worker timing.", "Correct. An atomic, deterministic check on the outgoing call prevents duplicates even when workers run in parallel."),
 ("p3_d.py", "The results arrive in the order requested, and a guarantee from the service", "x") if False else ("p3_d.py", "A guarantee from the service that results are returned in submission order.", "Relying on the order in which requests were submitted, since the service returns results in that order."),
 ("p3_b.py", "Split it into focused files under .claude/rules/ such as testing.md, api-conventions.md, and deployment.md, keeping only universal guidance in CLAUDE.md.",
             "Split it into focused files under .claude/rules/ such as testing.md and deployment.md, scoping topic files with paths frontmatter where they apply to certain files, and keep only universal guidance in CLAUDE.md."),
 ("p3_b.py", "Ask Claude to review each generated handler against the paragraph and fix deviations.", "Ask Claude to review each generated handler against the team's written conventions and fix deviations."),
 ("p3_b.py", "Self-review against the same ambiguous description does not remove the ambiguity.", "Self-review against prose rules leaves the same ambiguity in place."),
 # ---- Paper 4
 ("p4_b.py", "should read the diff, write a description file", "should read a saved diff file, write a description file") if False else ("p4_b.py", "that should read the diff, write a description file, and never run shell commands.", "that should read a diff file already saved in the repository, write a description file, and never run shell commands."),
 ("p4_b.py", "A developer's preference for brief explanations in the terminal and a specific commit message tone.", "A developer's preference for how long Claude's explanations are in their own terminal sessions."),
 ("p4_d.py", "Strict schemas via tool use have eliminated malformed JSON.", "Tool definitions use strict schema enforcement, so every tool input is syntactically valid and schema-conformant."),
 ("p4_c.py", "What approach best surfaces unconsidered concerns?", "What approach best surfaces unconsidered concerns before any code is written?"),
 ("p4_a.py", "and instead makes tool calls with made-up arguments. What is the better configuration?", "and instead makes tool calls with made-up arguments. The agent must still be able to answer in plain text when no tool is needed. What is the better configuration?"),
 ("p4_b.py", "Use plan mode whenever a task touches more than one file, even if the change is identical in each file and obvious.", "Use plan mode only when a task touches more than one file, and never for changes inside a single file."),
 ("p4_b.py", "A mechanical, well-understood change may not need planning, though scope matters.", "File count alone is not the criterion: a mechanical change repeated across files can be direct execution, and a single-file change can still need planning."),
 # ---- Paper 5
 ("p5_c.py", "Keep everything as is, because deploying automatically is what continuous integration means.", "Keep everything as is, because deploying automatically after tests pass is what continuous integration means."),
 ("p5_a.py", "Contradictory", "Contradictory") if False else ("p5_a.py", "Conflicting signals leave the examples dominant.", "Contradictory examples and instructions give unreliable results; replacing the examples addresses the cause."),
]
bad = 0
for f, old, new in FIXES:
    p = os.path.join(Q, f)
    s = open(p, encoding="utf-8").read()
    n = s.count(old)
    if n != 1:
        print("SKIP (%d matches): %s :: %s" % (n, f, old[:70])); bad += 1; continue
    open(p, "w", encoding="utf-8").write(s.replace(old, new))
print("done, unmatched:", bad)
