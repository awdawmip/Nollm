"""Rank Git-pinned file candidates from machine facts, with reproducible ablations."""
import argparse
from collections import defaultdict
from dataclasses import dataclass
import json
from math import log, sqrt
from pathlib import Path, PurePosixPath
import re


IDENT = re.compile(r"[A-Za-z][A-Za-z_0-9]*")
CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")
STOP = set("a an the where how why what do does is in for as to and or with project repo code file files src lib py test tests class def function from import new old single first this then next by same check changes between called".split())
COMMON_IDENT = set("python cpp sql http ui api cli test tests c cxx h web js html rust native url id yaml json".split())
ARCHIVE = {"artifacts", "archive", "archives", "evidence", "docs", "dist", "build", "vendor", "node_modules"}
LANG_SUFFIXES = {".py", ".cpp", ".h", ".hpp", ".cc", ".c", ".cs", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".sh", ".ps1", ".cmd", ".bat", ".toml", ".json", ".yaml", ".yml", ".sql", ".cmake", ".html", ".css", ".psd1", ".vue", ".rb", ".kt"}
FIELD_WEIGHTS = {"directory": .66, "filename": 1.95, "symbol": 1.32, "symbol_candidate": 1.15, "language": .48, "key": 1.65, "operand": 1.12, "predicate": .74, "evidence_path": .69}


def read_rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def wordforms(value, keep_stop=False):
    """Split a qualified symbol; keep joined identifiers and conservative plural forms."""
    out = set()
    for name in IDENT.findall(value):
        segments = CAMEL.findall(name.replace("_", " "))
        lower = name.lower()
        out.update([lower, lower.replace("_", "")])
        out.update(t for t in lower.split("_") if t)
        if len(segments) > 1:
            out.add("".join(w.lower() for w in segments))
        out.update(s.lower() for s in segments if len(s)>1 or s.isalpha())
    for term in tuple(out):
        if len(term)>5 and term.endswith("ies"):
            out.add(term[:-3] + "y")
        elif len(term)>4 and term.endswith("s") and not term.endswith(("ss","us","is")):
            out.add(term[:-1])
    return out if keep_stop else out - STOP


@dataclass(frozen=True)
class Fact:
    field: str
    value: str
    line: int


@dataclass(frozen=True)
class Concept:
    key: str
    terms: tuple
    weight: float


def load_aliases(paths):
    aliases = {}
    for file in paths:
        if file:
            for line in file.read_text(encoding="utf-8").splitlines():
                if line and not line.startswith("#"):
                    key, terms = line.split("\t", 1)
                    aliases[key] = tuple(terms.lower().split())
    return aliases


def concepts(query, aliases):
    parts = []
    spans = []
    # Longest query-side alias wins within a span; two separated concepts can both match.
    for phrase, targets in sorted(aliases.items(), key=lambda pair: (-len(pair[0]),pair[0])):
        for match in re.finditer(re.escape(phrase),query,re.I):
            left,right = match.span()
            if not any(left < end and start < right for start,end in spans):
                spans.append((left,right))
                parts.append(Concept(phrase,targets,.83))
    anchors = []
    for match in IDENT.finditer(query):
        if any(left <= match.start() < right for left,right in spans):
            continue
        value = match.group()
        stripped = value.lower().replace("_","")
        if stripped in STOP:
            continue
        terms = wordforms(value)
        if not terms:
            continue
        structured = "_" in value or any(c.isdigit() for c in value) or bool(re.search("[a-z][A-Z]", value))
        is_anchor = structured or value.isupper() and len(value)>=3 or bool(re.search(r"[\u3400-\u9fff]",query)) and len(value)>=3
        if is_anchor and stripped not in COMMON_IDENT:
            anchors.append((stripped,structured))
        parts.append(Concept(value, (value.lower(), stripped), 1.4 if is_anchor else 1.0))
        if structured:
            for piece in CAMEL.findall(value.replace("_"," ")):
                if len(piece)>1 and piece.lower() not in STOP and piece.lower()!=stripped:
                    parts.append(Concept(piece, (piece.lower(),), .70))
    # Repeated spelling variants in a prompt cannot inflate a score.
    dedup = {}
    for part in parts:
        tag = tuple(sorted(set(part.terms)))
        if tag not in dedup or part.weight > dedup[tag].weight:
            dedup[tag] = part
    return list(dedup.values()), anchors


class Terms:
    def __init__(self):
        self.postings = defaultdict(dict)
        self.docs = set()

    def add(self, idx, field, value, line=0):
        fact = Fact(field,value,line)
        for token in wordforms(value):
            entries = self.postings[token]
            old = entries.get(idx)
            if old is None or FIELD_WEIGHTS[field] > FIELD_WEIGHTS[old.field]:
                entries[idx]=fact
        self.docs.add(idx)

    def match(self, query):
        contributions = defaultdict(list)
        total = len(self.docs)
        for concept in query:
            winners = {}
            for term in sorted(set(concept.terms)):
                post = self.postings.get(term,{})
                if not post:
                    continue
                idf = min(8.0,log(1+(total+.5)/(len(post)+.5)))
                for idx, fact in post.items():
                    score = idf * concept.weight * FIELD_WEIGHTS[fact.field]
                    if idx not in winners or score > winners[idx][0]:
                        winners[idx] = (score,term,fact)
            for idx,(score,term,fact) in winners.items():
                contributions[idx].append((score,concept.key,term,fact))
        return contributions


def rank_value(parts):
    return sum(c[0] for c in parts)*(1+min(.55,.09*(len(parts)-1)))


def path_prior(path):
    pieces=PurePosixPath(path)
    if any(s.lower() in ARCHIVE for s in pieces.parts):
        return .53
    if pieces.suffix.lower() not in LANG_SUFFIXES and pieces.name not in {"Makefile","CMakeLists.txt","Dockerfile"}:
        return .43
    if pieces.stem in {"__init__","main","index"}:
        return .94
    return 1.


def number(score):
    return round(score,5)


class Router:
    def __init__(self, facts, records=None, aliases=None, mode="semantic"):
        self.mode = mode
        manifest=json.loads((facts/"manifest.json").read_text(encoding="utf-8"))
        self.commit=manifest["commit"]
        default=Path(__file__).resolve().with_name("query-lexicon.tsv")
        domain=facts.parent/"query-aliases.tsv" if aliases is None else aliases
        self.aliases=load_aliases([default,domain if domain and domain.is_file() else None])
        self.files={}
        self.prior={}
        self.terms=Terms()
        self.adj=defaultdict(dict)
        self.claim_terms=Terms()
        self.claims={}
        for data in read_rows(facts/"files.jsonl"):
            path=data["path"]
            if data["mode"] not in ("100644","100755"):
                continue
            self.files[path]=data["blob"]
            self.prior[path]=path_prior(path)
            obj=PurePosixPath(path)
            self.terms.add(path,"filename",obj.stem)
            # A repeated run name in an archived directory must not overwhelm a filename hit.
            self.terms.add(path,"directory",str(obj.parent))
            language = {"header":"header c cpp","cpp":"cpp cxx","python":"python","js":"javascript js"}.get(data["lang"],data["lang"])
            self.terms.add(path,"language",language)
        for symbol in read_rows(facts/"symbols.jsonl"):
            file=symbol["path"]
            if self.files.get(file)==symbol["blob"]:
                field = "symbol_candidate" if symbol["kind"].endswith("candidate") else "symbol"
                self.terms.add(file,field,symbol["name"],symbol["line"])
        if mode in {"graph","semantic"}:
            self._load_graph(facts/"edges.jsonl")
        if mode=="semantic":
            if records is None:
                raise ValueError("semantic mode requires --records")
            for record in read_rows(records):
                self._add_record(record)

    def _load_graph(self, file):
        for edge in read_rows(file):
            src,dst=edge["src"],edge["dst"]
            if (edge["confidence"]!="exact" or src==dst or self.files.get(src)!=edge["src_blob"]
                    or self.files.get(dst)!=edge["dst_blob"]):
                continue
            for node,neighbor,direction in ((src,dst,"out"),(dst,src,"in")):
                saved=self.adj[node].get(neighbor)
                witness=(edge["rel"],direction,edge["line"],edge["token"])
                if saved is None or witness<saved:
                    self.adj[node][neighbor]=witness

    def _add_record(self, row):
        if row["kind"]!="reviewed" or not row["evidence"] or row["commit"]!=self.commit:
            return
        if any(self.files.get(r["path"])!=r["blob"] for r in row["evidence"]):
            return
        key=row["key"]
        self.claims[key]=row
        self.claim_terms.add(key,"key",key)
        for subject,predicate,obj in row["atoms"]:
            self.claim_terms.add(key,"operand",subject)
            self.claim_terms.add(key,"predicate",predicate)
            self.claim_terms.add(key,"operand",obj)
        for ref in row["evidence"]:
            self.claim_terms.add(key,"evidence_path",PurePosixPath(ref["path"]).stem)

    def _propagate(self, lexical):
        result={}
        for seed,base in sorted(lexical.items(),key=lambda x:(-x[1],x[0]))[:12]:
            for dst,witness in self.adj.get(seed,{}).items():
                # Damp hubs, retain both directions. Only one strongest witness is counted.
                den=sqrt(1+.07*len(self.adj[seed])+.04*len(self.adj[dst]))
                score=.44*base/den
                if dst not in result or score>result[dst][0]:
                    result[dst]=(score,seed,witness)
        return result

    def _claimed(self, query):
        result={}
        ranked = self.claim_terms.match(query)
        winners=sorted(((rank_value(x),key) for key,x in ranked.items()), key=lambda x:(-x[0],x[1]))[:3]
        for value,key in winners:
            hits=ranked[key]
            if len(hits)<2 or value<min(6.4, 1+1.2*log(1+len(self.claims))):
                continue
            for index,ref in enumerate(self.claims[key]["evidence"]):
                score=value*.96/(1+.14*index)
                dst=ref["path"]
                if dst not in result or score>result[dst][0]:
                    result[dst]=(score,key,ref["role"],sorted(p[1] for p in hits))
        return result

    def query(self, text, limit=5):
        if not (1<=limit<=5):
            raise ValueError("limit must be between 1 and 5")
        result={"query":text,"commit":self.commit,"status":"abstain","paths":[],"hits":[]}
        query,anchors=concepts(text,self.aliases)
        unknown=[term for term,_ in anchors if term not in self.terms.postings and term not in self.claim_terms.postings]
        if unknown:
            return dict(result,reason="unobserved_identifier",unobserved=sorted(set(unknown)))
        found=self.terms.match(query)
        lexical={p:rank_value(v)*self.prior[p] for p,v in found.items()}
        graph=self._propagate(lexical) if self.mode!="lexical" else {}
        claims=self._claimed(query) if self.mode=="semantic" else {}
        scores={}
        for p in set(lexical)|set(graph)|set(claims):
            score=lexical.get(p,0.)+graph.get(p,(0,))[0]+claims.get(p,(0,))[0]
            scores[p]=score
        if not scores or max(scores.values())<min(3.8, 1+log(1+len(self.files))):
            return dict(result,reason="weak_or_empty_match")
        order=sorted(scores,key=lambda p:(-scores[p],p))[:limit]
        hits=[]
        for p in order:
            ev=sorted(found.get(p,[]),key=lambda a:(-a[0],a[1],a[2]))
            hit={"path":p,"blob":self.files[p],"score":number(scores[p]),"parts":{
                "tags":number(lexical.get(p,0.)),"edge":number(graph.get(p,(0.,))[0]),
                "claim":number(claims.get(p,(0.,))[0])},
                "tags":[{"query":group,"term":term,"field":fact.field,"at":fact.value,"line":fact.line,"score":number(value)}
                        for value,group,term,fact in ev]}
            if p in graph:
                _,seed,(rel,direction,line,token)=graph[p]
                hit["edge"]={"seed":seed,"direction":direction,"relation":rel,"line":line,"token":token}
            if p in claims:
                _,key,role,terms=claims[p]
                hit["claim"]={"key":key,"role":role,"matched":terms}
            hits.append(hit)
        return dict(result,status="ok",hits=hits,paths=order)


def main():
    import subprocess
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--facts",type=Path,required=True)
    parser.add_argument("--records",type=Path)
    parser.add_argument("--aliases",type=Path,help="additional TSV query vocabulary, defaults to query-aliases.tsv next to the facts directory")
    parser.add_argument("--mode",choices=("lexical","graph","semantic"),default="graph")
    parser.add_argument("--repo",type=Path,help="check corpus commit against this Git checkout")
    parser.add_argument("--rev",help="Git revision for --repo (default HEAD)")
    parser.add_argument("--limit",type=int,default=5)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--queries",type=Path)
    group.add_argument("--query")
    parser.add_argument("--out",type=Path)
    a=parser.parse_args()
    if a.rev and not a.repo:
        parser.error("--rev requires --repo")
    try:
        if a.aliases is not None and not a.aliases.is_file():
            raise ValueError("--aliases file does not exist")
        if a.repo:
            lookup=subprocess.run(["git","-C",str(a.repo),"rev-parse","--verify","--end-of-options",(a.rev or "HEAD")+"^{commit}"],capture_output=True,text=True)
            if lookup.returncode:
                raise ValueError("unable to resolve requested Git revision")
            pinned=json.loads((a.facts/"manifest.json").read_text(encoding="utf-8"))["commit"]
            if lookup.stdout.strip()!=pinned:
                raise ValueError("machine facts belong to a different Git revision; rebuild or select matching --rev")
        engine=Router(a.facts,a.records,a.aliases,a.mode)
        if a.query is not None:
            requests=[{"id":"1","query":a.query}]
        else:
            requests=json.loads(a.queries.read_text(encoding="utf-8"))
        if not isinstance(requests,list):
            raise ValueError("--queries requires an array of {id, query} objects")
        results=[]
        for request in requests:
            if not isinstance(request.get("query"),str) or not request["query"].strip():
                raise ValueError("query must be a non-empty string")
            results.append({"id":request["id"],**engine.query(request["query"],a.limit)})
        payload=json.dumps({"mode":a.mode,"commit":engine.commit,"results":results},ensure_ascii=False,separators=(",",":"))+"\n"
        if a.out:
            a.out.write_text(payload,encoding="utf-8")
        else:
            print(payload,end="")
    except (OSError,KeyError,ValueError) as exc:
        parser.exit(2, f"router: {exc}\n")


if __name__=="__main__":
    main()
