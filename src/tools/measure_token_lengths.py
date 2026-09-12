import json, os, gzip, statistics, collections, csv
from tokenizers import Tokenizer
tok = Tokenizer.from_file(os.path.expanduser("~/.cache/huggingface/hub/models--RedHatAI--gemma-4-12B-it-NVFP4/snapshots/8965ad1c93dccb43e05e7882d98f2d32c0dd434d/tokenizer.json"))
recs=[json.loads(l) for l in gzip.open("open/train_unlabeled.jsonl.gz","rt",encoding="utf-8")]
texts=["\n".join(d["text"] for d in r["docs"]) for r in recs]
encs=tok.encode_batch(texts, add_special_tokens=False)
ns=[len(e.ids) for e in encs]
# per-doc-type
bytype=collections.defaultdict(list); ndocs=[]
for r in recs:
    ndocs.append(len(r["docs"]))
    for d in r["docs"]:
        bytype[d["type"]].append(len(tok.encode(d["text"],add_special_tokens=False).ids))
out=os.environ["S"]+"/train_lengths.csv"
with open(out,"w",newline="") as f:
    w=csv.writer(f); w.writerow(["id","n_docs","chars","tokens","dropped"])
    for r,t,n in zip(recs,texts,ns): w.writerow([r["id"],len(r["docs"]),len(t),n,json.dumps(r.get("dropped_doc_counts"),ensure_ascii=False)])
s=sorted(ns); N=len(s)
q=lambda p: s[min(N-1,int(N*p))]
print("N",N,"total tokens",sum(ns))
print("min",s[0],"p10",q(.1),"p25",q(.25),"median",q(.5),"mean",round(statistics.mean(ns)),"p75",q(.75),"p90",q(.9),"p95",q(.95),"p99",q(.99),"max",s[-1])
for th in [4000,8000,12000,16384,20000,24000,28000,32768]:
    c=sum(n>th for n in ns); print(f">{th:>6}: {c:>6} ({c/N*100:5.1f}%)")
print("\nhistogram (2k bins)")
for lo in range(0,s[-1]+2000,2000):
    c=sum(lo<=n<lo+2000 for n in ns)
    if c: print(f"{lo:>6}-{lo+2000:<6} {c:>6} {'#'*(c//100)}")
print("\nper doc type: count / median / p90 / max")
for k,v in sorted(bytype.items(), key=lambda x:-len(x[1])):
    v=sorted(v); print(f"{k:<8} {len(v):>6} {v[len(v)//2]:>7} {v[int(len(v)*.9)]:>7} {v[-1]:>7}")
print("\ndocs per record:", collections.Counter(ndocs).most_common())
print("dropped non-empty:", sum(1 for r in recs if r.get("dropped_doc_counts")))
print("chars/token", round(sum(map(len,texts))/sum(ns),2))
