import os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXES = [
 ("questions/patches_c.py", "The research question and the instruction 'summarize everything found so far', since the subagent can look up the rest from the shared workspace when it starts.",
                           "The research question and the instruction 'summarize everything found so far', with no findings included in the prompt."),
 ("questions/p5_b.py", "The subagent has no access to what was found.", "Subagents do not inherit the coordinator's context, so without the findings in the prompt it has nothing to summarize."),
 ("questions/patches_c.py", "Percentages above 90 are always unreliable because accuracy cannot be measured accurately at that level, so any figure that high should be discounted by half.",
                           "The figure is sufficient if the review sample is large, because a big sample makes per-category breakdowns unnecessary."),
 ("questions/p5_c.py", "Accuracy can be measured at any level with adequate data.", "A large sample still does not show whether particular categories perform worse than the average."),
 ("questions/patches_c.py", "To give reviewers more work so that their skills stay sharp and the review team keeps a steady workload throughout the year, which management prefers.",
                           "To reduce the number of low-confidence records that need review by retraining the reviewers, which management prefers."),
 ("questions/p5_d.py", "To confirm that the model's confidence scores are exactly 1.0 for all accepted records.", "To confirm that the confidence threshold can be raised without checking any real outcomes."),
 ("questions/patches_c.py", ' "P5-Q38": {1:', ' "P5-Q38": {0: "Use a token limited to reading code and posting PR comments, and keep branch and settings write access out of that job.", 1:'),
 ("questions/patches_c.py", "Because skipped verification exposes data and enables wrong financial actions, add a programmatic prerequisite; prompts can reduce but never eliminate the failure rate.",
                           "Because skipped verification exposes data and enables wrong financial actions, add a programmatic prerequisite gate rather than relying on prompts."),
 ("questions/patches_c.py", "Accept 4% for now and continue adding examples, since each additional example is likely to halve the remaining failures until they eventually reach zero within a few weeks.",
                           "Keep adding examples until skipped verification is below 1%, then re-evaluate, since each new example should cut the failure rate further."),
 ("questions/p5_c.py", "Leadership says the goal is continuous integration and a human-approved release process. What should be changed?",
                       "Which change keeps automated build, test, and review on every PR while making production release a human decision?"),
 ("questions/patches_c.py", "Keep automated build, test, and review on every PR (CI), but add a manual approval gate before production, which makes the release continuous delivery.",
                           "Keep automated build, test, and review on every PR, but add a manual approval gate before production deployment."),
 # P3-Q17 labels
 ("questions/p3_b.py", "(A) rename a method used in one file, (B) explain a single function's behavior, (C) survey five independent services", "(1) rename a method used in one file, (2) explain a single function's behavior, (3) survey five independent services"),
 ("questions/p3_b.py", "then compare them, (D) make a tightly coupled edit", "then compare them, (4) make a tightly coupled edit"),
 ("questions/p3_b.py", "Which task best justifies multiple agents?", "Which task best justifies multiple agents?"),
 ("questions/p3_b.py", "Task C, because the services are independent", "Task 3, because the services are independent"),
 ("questions/p3_b.py", "Task B, because explanation is easier", "Task 2, because explanation is easier"),
 ("questions/p3_b.py", "Task D, because tightly coupled edits", "Task 4, because tightly coupled edits"),
 ("questions/patches_b.py", "Task A, because delegating even small edits to a subagent ensures that every change is reviewed by a second agent before it is applied, which improves safety.",
                           "Task 1, because delegating even a small edit to a subagent isolates it from the main context and keeps that context clean."),
 ("questions/p3_b.py", "Task A, because delegating even small edits ensures that every change is reviewed by a second agent.", "Task 1, because delegating even a small edit isolates it from the main context."),
]
bad = 0
for f, old, new in FIXES:
    p = os.path.join(R, f)
    s = open(p, encoding="utf-8").read()
    n = s.count(old)
    if n != 1:
        print("SKIP (%d): %s :: %s" % (n, f, old[:60])); bad += 1; continue
    open(p, "w", encoding="utf-8").write(s.replace(old, new))
print("unmatched", bad)
