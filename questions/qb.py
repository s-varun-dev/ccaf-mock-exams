"""Authoring helpers. Each question file calls Q(...) with options written correct-first;
build_bank.py shuffles options (balanced) so authoring order never leaks the answer."""
REGISTRY = []


def O(text, ok, exp):
    return dict(text=text, ok=bool(ok), exp=exp)


def Q(qid, task, stem, opts, why, concept, reasoning, lesson, diff=None):
    REGISTRY.append(dict(id=qid, task=task, stem=stem, opts=opts, why=why,
                         concept=concept, reasoning=reasoning, lesson=lesson, diff=diff))
