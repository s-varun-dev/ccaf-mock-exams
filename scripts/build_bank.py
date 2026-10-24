"""Merge blueprint + authored questions -> data/question_bank.json (options shuffled with balanced answer positions)."""
import json, random, re, sys, os, collections, importlib, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "questions"))
import qb

SCEN_NAMES = {1: "Customer Support Resolution Agent", 2: "Code Generation with Claude Code",
              3: "Multi-Agent Research System", 4: "Developer Productivity with Claude",
              5: "Claude Code for Continuous Integration", 6: "Structured Data Extraction"}
DOM_NAMES = {1: "Agentic Architecture & Orchestration", 2: "Tool Design & MCP Integration",
             3: "Claude Code Configuration & Workflows", 4: "Prompt Engineering & Structured Output",
             5: "Context Management & Reliability"}
LET = "ABCDEF"


def load():
    for f in sorted(glob.glob(os.path.join(ROOT, "questions", "p[0-9]_*.py"))):
        importlib.import_module(os.path.basename(f)[:-3])


def main():
    load()
    bp = {b["id"]: b for b in json.load(open(os.path.join(ROOT, "data", "blueprint.json")))}
    authored = {q["id"]: q for q in qb.REGISTRY}
    from patches import PATCH
    import patches_b, patches_c
    for src, skip4 in ((PATCH, True), (patches_b.PATCH, False), (patches_c.PATCH, False)):
        for qid, pm in src.items():
            if qid in authored and not (skip4 and int(qid[-2:]) % 4 == 1):  # P1: leave every 4th unpatched (avoid reverse tell)
                for idx, txt in pm.items():
                    authored[qid]["opts"][idx]["text"] = txt
    assert len(authored) == len(qb.REGISTRY), "duplicate authored ids"
    rng = random.Random(777)
    out = []
    # balanced target positions for single-answer items, per paper
    for p in range(1, 6):
        ids = sorted(i for i in authored if i.startswith(f"P{p}-"))
        singles = [i for i in ids if bp[i]["kind"] == "S"]
        pos = [LET[k % 4] for k in range(len(singles))]
        rng.shuffle(pos)
        target = dict(zip(singles, pos))
        for i in ids:
            a, b = authored[i], bp[i]
            n_ok = sum(o["ok"] for o in a["opts"])
            kind = {1: "S", 2: "M2", 3: "M3"}[n_ok]
            assert kind == b["kind"], f"{i}: authored kind {kind} != blueprint {b['kind']}"
            assert int(a["task"].split(".")[0]) == b["domain"], f"{i}: task {a['task']} vs domain {b['domain']}"
            n_opts = {"S": 4, "M2": 5, "M3": 6}[kind]
            assert len(a["opts"]) == n_opts, f"{i}: {len(a['opts'])} options"
            opts = list(a["opts"])
            for attempt in range(500):
                rng.shuffle(opts)
                letters = [LET[k] for k, o in enumerate(opts) if o["ok"]]
                if kind == "S" and letters[0] != target[i]:
                    continue
                break
            correct = "".join(LET[k] for k, o in enumerate(opts) if o["ok"])
            sec = sorted({int(t.split(".")[0]) for t in re.findall(r"Task ([\d\.]+(?:, [\d\.]+)*)", a["concept"])
                          for t in re.split(r", ", t)} - {b["domain"]})
            out.append(dict(
                id=i, paper=b["paper"], number=b["num"], scenario=b["scenario"],
                scenario_name=SCEN_NAMES[b["scenario"]], primary_domain=b["domain"],
                primary_domain_name=DOM_NAMES[b["domain"]], secondary_domains=sec, task_statement=a["task"],
                difficulty=a["diff"] or b["difficulty"], response_type=kind,
                select_count={"S": 1, "M2": 2, "M3": 3}[kind], theme_hint=b["theme"],
                stem=a["stem"],
                options=[dict(letter=LET[k], text=o["text"], correct=o["ok"], explanation=o["exp"]) for k, o in enumerate(opts)],
                correct=correct, why_correct=a["why"], key_concept=a["concept"], exam_reasoning=a["reasoning"],
                production_lesson=a["lesson"],
                source_rationale="Original item written against official exam guide task statement %s (CCAR-F v1.0)." % a["task"],
                verification_status="authored"))
    out.sort(key=lambda q: (q["paper"], q["number"]))
    json.dump(out, open(os.path.join(ROOT, "data", "question_bank.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    # quick stats
    by = collections.defaultdict(list)
    for q in out:
        by[q["paper"]].append(q)
    for p, qs in sorted(by.items()):
        c = collections.Counter(l for q in qs if q["response_type"] == "S" for l in q["correct"])
        longest = 0
        for q in qs:
            if q["response_type"] != "S":
                continue
            lens = {o["letter"]: len(o["text"]) for o in q["options"]}
            if lens[q["correct"]] == max(lens.values()):
                longest += 1
        print(f"P{p}: {len(qs)} q, single-answer position counts {dict(sorted(c.items()))}, correct-is-longest {longest}/{sum(q['response_type']=='S' for q in qs)}")
    print("total", len(out))


if __name__ == "__main__":
    main()
