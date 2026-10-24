"""Builds the 300-slot blueprint (scenario x domain x task statement x difficulty x response type)."""
import json, random, itertools, collections
random.seed(20260724)
DOM_TARGET = [16, 11, 12, 12, 9]
PAPER_SCEN = {1:[1,2,3,4], 2:[1,2,5,6], 3:[3,4,5,6], 4:[1,2,4,6], 5:[2,3,5,6]}
# (min,max) per domain D1..D5 for each scenario
RANGE = {
 1:[(3,8),(2,5),(0,0),(0,4),(2,5)],
 2:[(0,3),(0,3),(5,12),(0,3),(1,4)],
 3:[(4,8),(2,5),(0,0),(0,4),(2,5)],
 4:[(1,5),(2,6),(2,7),(0,3),(1,3)],
 5:[(0,3),(0,2),(3,7),(4,8),(0,2)],
 6:[(0,3),(1,4),(0,0),(5,9),(2,5)],
}
TASKS = {
 (1,1):["1.4","1.1","1.5","1.6","1.7"],(1,2):["2.1","2.2","2.3","2.4"],(1,4):["4.2","4.1"],(1,5):["5.2","5.1"],
 (2,1):["1.7","1.6"],(2,2):["2.4","2.5"],(2,3):["3.1","3.2","3.3","3.4","3.5"],(2,4):["4.2"],(2,5):["5.4","5.1"],
 (3,1):["1.2","1.3","1.6","1.1","1.7"],(3,2):["2.1","2.2","2.3","2.4"],(3,4):["4.2","4.6"],(3,5):["5.3","5.6","5.1"],
 (4,1):["1.2","1.6","1.7","1.3"],(4,2):["2.5","2.4","2.1","2.3"],(4,3):["3.2","3.4","3.1","3.3","3.5"],(4,4):["4.2"],(4,5):["5.4","5.1"],
 (5,1):["1.6"],(5,2):["2.4","2.2"],(5,3):["3.6","3.5"],(5,4):["4.1","4.2","4.3","4.4","4.5","4.6"],(5,5):["5.5"],
 (6,1):["1.6","1.5"],(6,2):["2.3","2.2","2.1"],(6,4):["4.3","4.4","4.2","4.5"],(6,5):["5.5","5.1","5.6"],
}
THEMES = ["works-design","system-fails","partial-failure","misleading-result","missing-handoff","unsafe-tool-call",
          "duplicate-side-effect-retry","valid-but-wrong-output","unnecessary-agents","human-intervention"]
def solve(scens):
    import itertools
    rows={}
    for s in scens[:-1]:
        rng=RANGE[s]
        opts=[r for r in itertools.product(*[range(lo,hi+1) for lo,hi in rng]) if 13<=sum(r)<=17]
        random.shuffle(opts); rows[s]=opts
    last=scens[-1]
    def rec(i,acc):
        if i==len(scens)-1:
            r=tuple(t-a for t,a in zip(DOM_TARGET,acc))
            if all(lo<=x<=hi for x,(lo,hi) in zip(r,RANGE[last])) and 13<=sum(r)<=17: return [r]
            return None
        for r in rows[scens[i]]:
            na=[a+b for a,b in zip(acc,r)]
            if any(x>t for x,t in zip(na,DOM_TARGET)): continue
            res=rec(i+1,na)
            if res is not None: return [r]+res
        return None
    res=rec(0,[0]*5)
    if res is None: raise SystemExit("no solution %s"%scens)
    return {s:list(r) for s,r in zip(scens,res)}
usage=collections.Counter()
bp=[]
for p,scens in PAPER_SCEN.items():
    mat=solve(scens)
    diffs=["F"]*12+["I"]*33+["C"]*15
    random.shuffle(diffs)
    kinds=["S"]*54+["M2"]*5+["M3"]*1
    random.shuffle(kinds)
    themes=(THEMES*6)[:60]; random.shuffle(themes)
    slots=[]
    for s in scens:
        for d in range(1,6):
            for _ in range(mat[s][d-1]):
                cands=TASKS[(s,d)]
                t=min(cands,key=lambda x:(usage[x],random.random())); usage[t]+=1
                slots.append((s,d,t))
    # order: by scenario in listed order, domain order inside
    for n,(s,d,t) in enumerate(slots,1):
        bp.append(dict(id=f"P{p}-Q{n:02d}",paper=p,num=n,scenario=s,domain=d,task=t,
                       difficulty=diffs[n-1],kind=kinds[n-1],theme=themes[n-1]))
json.dump(bp,open("data/blueprint.json","w"),indent=1)
for p in PAPER_SCEN:
    rows=[b for b in bp if b["paper"]==p]
    print(p,PAPER_SCEN[p],collections.Counter(b["domain"] for b in rows),collections.Counter(b["scenario"] for b in rows),collections.Counter(b["difficulty"] for b in rows),collections.Counter(b["kind"] for b in rows))
print(sorted(usage.items()))
